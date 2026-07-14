// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// MecanumPicoHardware — full ros2_control SystemInterface implementation.
// Handles 4 wheels (front_left, front_right, rear_left, rear_right) and,
// if declared in the URDF, one IMU sensor (accel + gyro, ICM-20948 via Pico).
// Communicates with the Raspberry Pi Pico via USB-CDC.
// Host sends velocity targets; PID loops run on-Pico.

#include "mecanum_pico/mecanum_pico.hpp"

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/logging.hpp"

#include <cmath>
#include <vector>

namespace mecanum_pico
{

// =============================================================================
// on_init — load parameters, configure wheel objects
// =============================================================================
hardware_interface::CallbackReturn MecanumPicoHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
    hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // --- Load hardware parameters from URDF --------------------------------
  cfg_.front_left_wheel_name = info_.hardware_parameters.at("front_left_wheel_name");
  cfg_.front_right_wheel_name = info_.hardware_parameters.at("front_right_wheel_name");
  cfg_.rear_left_wheel_name = info_.hardware_parameters.at("rear_left_wheel_name");
  cfg_.rear_right_wheel_name = info_.hardware_parameters.at("rear_right_wheel_name");

  cfg_.loop_rate = std::stof(info_.hardware_parameters.at("loop_rate"));
  cfg_.device = info_.hardware_parameters.at("device");
  cfg_.baud_rate = std::stoi(info_.hardware_parameters.at("baud_rate"));
  cfg_.timeout_ms = std::stoi(info_.hardware_parameters.at("timeout_ms"));
  cfg_.enc_counts_per_rev = std::stoi(info_.hardware_parameters.at("enc_counts_per_rev"));

  // --- Configure wheel data structures -----------------------------------
  wheel_fl_.setup(cfg_.front_left_wheel_name, cfg_.enc_counts_per_rev);
  wheel_fr_.setup(cfg_.front_right_wheel_name, cfg_.enc_counts_per_rev);
  wheel_rl_.setup(cfg_.rear_left_wheel_name, cfg_.enc_counts_per_rev);
  wheel_rr_.setup(cfg_.rear_right_wheel_name, cfg_.enc_counts_per_rev);

  // --- Validate joint declarations in URDF --------------------------------
  for (const hardware_interface::ComponentInfo & joint : info_.joints) {
    if (joint.command_interfaces.size() != 1) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Joint '%s' has %zu command interfaces — expected exactly 1.",
        joint.name.c_str(), joint.command_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Joint '%s' has command interface '%s' — expected 'velocity'.",
        joint.name.c_str(), joint.command_interfaces[0].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces.size() != 2) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Joint '%s' has %zu state interfaces — expected 2 (position + velocity).",
        joint.name.c_str(), joint.state_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Joint '%s' first state interface is '%s' — expected 'position'.",
        joint.name.c_str(), joint.state_interfaces[0].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Joint '%s' second state interface is '%s' — expected 'velocity'.",
        joint.name.c_str(), joint.state_interfaces[1].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  // --- Detect optional IMU sensor block in URDF --------------------------
  // A sensor is only wired up if the URDF actually declares one under this
  // <ros2_control> block (see gubot_one/description/urdf/ros2_control_hardware.xacro).
  if (!info_.sensors.empty()) {
    const hardware_interface::ComponentInfo & sensor = info_.sensors[0];

    // 10-interface layout (like the sim xacro): accel + gyro + orientation.
    // Orientation is COMPUTED here (complementary filter) — the ICM-20948
    // does not measure it, but the Humble imu_sensor_broadcaster requires
    // orientation.x/y/z/w to activate.
    // ALT: exactly 6 interfaces (accel + gyro) — the imu_broadcaster could
    //      never activate on real hardware. 6 is still accepted (legacy).
    static const char * const kExpectedImuInterfaces[10] = {
      "linear_acceleration.x", "linear_acceleration.y", "linear_acceleration.z",
      "angular_velocity.x", "angular_velocity.y", "angular_velocity.z",
      "orientation.x", "orientation.y", "orientation.z", "orientation.w"
    };

    const size_t n_ifaces = sensor.state_interfaces.size();
    if (n_ifaces != 6 && n_ifaces != 10) {
      RCLCPP_FATAL(
        rclcpp::get_logger("MecanumPicoHardware"),
        "Sensor '%s' declares %zu state interfaces — expected 6 "
        "(accel + gyro) or 10 (accel + gyro + orientation).",
        sensor.name.c_str(), n_ifaces);
      return hardware_interface::CallbackReturn::ERROR;
    }

    for (size_t i = 0; i < n_ifaces; ++i) {
      if (sensor.state_interfaces[i].name != kExpectedImuInterfaces[i]) {
        RCLCPP_FATAL(
          rclcpp::get_logger("MecanumPicoHardware"),
          "Sensor '%s' state interface %zu is '%s' — expected '%s'. "
          "Check the order in ros2_control_hardware.xacro.",
          sensor.name.c_str(), i, sensor.state_interfaces[i].name.c_str(),
          kExpectedImuInterfaces[i]);
        return hardware_interface::CallbackReturn::ERROR;
      }
    }

    imu_sensor_name_ = sensor.name;
    has_imu_sensor_ = true;
    has_orientation_ = (n_ifaces == 10);
    if (has_orientation_) {
      RCLCPP_INFO(
        rclcpp::get_logger("MecanumPicoHardware"),
        "IMU sensor '%s' found in URDF — accel/gyro via Pico 'i' command, "
        "orientation via onboard complementary filter.",
        imu_sensor_name_.c_str());
    } else {
      RCLCPP_WARN(
        rclcpp::get_logger("MecanumPicoHardware"),
        "IMU sensor '%s' declares only 6 interfaces (no orientation) — "
        "an imu_sensor_broadcaster will fail to activate. Declare the 4 "
        "orientation interfaces in the URDF to enable it.",
        imu_sensor_name_.c_str());
    }
  } else {
    RCLCPP_WARN(
      rclcpp::get_logger("MecanumPicoHardware"),
      "No <sensor> declared in URDF — IMU state interfaces will NOT be exported. "
      "An imu_broadcaster relying on '%s' will fail to activate.",
      imu_sensor_name_.c_str());
  }

  RCLCPP_INFO(
    rclcpp::get_logger("MecanumPicoHardware"),
    "on_init OK — device: %s  baud: %d  enc/rev: %d",
    cfg_.device.c_str(), cfg_.baud_rate, cfg_.enc_counts_per_rev);

  return hardware_interface::CallbackReturn::SUCCESS;
}

// =============================================================================
// export_state_interfaces — position + velocity for all 4 wheels
// =============================================================================
std::vector<hardware_interface::StateInterface>
MecanumPicoHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (Wheel * w : {&wheel_fl_, &wheel_fr_, &wheel_rl_, &wheel_rr_}) {
    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        w->name, hardware_interface::HW_IF_POSITION, &w->pos));
    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        w->name, hardware_interface::HW_IF_VELOCITY, &w->vel));
  }

  // --- IMU sensor (only if a <sensor> block was found in on_init) ---------
  if (has_imu_sensor_) {
    static const char * const kImuInterfaceNames[6] = {
      "linear_acceleration.x", "linear_acceleration.y", "linear_acceleration.z",
      "angular_velocity.x", "angular_velocity.y", "angular_velocity.z"
    };
    for (size_t i = 0; i < imu_data_.size(); ++i) {
      state_interfaces.emplace_back(
        hardware_interface::StateInterface(
          imu_sensor_name_, kImuInterfaceNames[i], &imu_data_[i]));
    }

    // Orientation (computed by the complementary filter in read()) — only
    // when the URDF declares the 10-interface layout. Required by the
    // Humble imu_sensor_broadcaster.
    if (has_orientation_) {
      static const char * const kOrientationNames[4] = {
        "orientation.x", "orientation.y", "orientation.z", "orientation.w"
      };
      for (size_t i = 0; i < imu_orientation_.size(); ++i) {
        state_interfaces.emplace_back(
          hardware_interface::StateInterface(
            imu_sensor_name_, kOrientationNames[i], &imu_orientation_[i]));
      }
    }
  }

  // 8 wheel state interfaces (4 wheels × 2) + 6 or 10 IMU state interfaces
  return state_interfaces;
}

// =============================================================================
// export_command_interfaces — velocity command for all 4 wheels
// =============================================================================
std::vector<hardware_interface::CommandInterface>
MecanumPicoHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (Wheel * w : {&wheel_fl_, &wheel_fr_, &wheel_rl_, &wheel_rr_}) {
    command_interfaces.emplace_back(
      hardware_interface::CommandInterface(
        w->name, hardware_interface::HW_IF_VELOCITY, &w->cmd));
  }

  // 4 command interfaces total
  return command_interfaces;
}

// =============================================================================
// on_configure — open serial port
// =============================================================================
hardware_interface::CallbackReturn MecanumPicoHardware::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Configuring...");
  if (comms_.connected()) {
    comms_.disconnect();
  }
  comms_.connect(cfg_.device, cfg_.baud_rate, cfg_.timeout_ms);

  // Health reporting (/diagnostics) for the serial link + control-loop
  // rate. Created fresh on every on_configure() so a previous run's
  // failure counters don't leak across reconfigurations.
  diagnostics_ = std::make_unique<HardwareDiagnostics>(
    get_name(), cfg_.device, cfg_.baud_rate, cfg_.loop_rate);
  diagnostics_->set_connected(comms_.connected());
  diagnostics_->start();

  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Successfully configured.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// =============================================================================
// on_cleanup — close serial port
// =============================================================================
hardware_interface::CallbackReturn MecanumPicoHardware::on_cleanup(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Cleaning up...");
  if (comms_.connected()) {
    comms_.disconnect();
  }
  if (diagnostics_) {
    diagnostics_->stop();
    diagnostics_.reset();
  }
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Successfully cleaned up.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// =============================================================================
// on_activate — verify connection; send sync byte
// =============================================================================
hardware_interface::CallbackReturn MecanumPicoHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Activating...");
  if (!comms_.connected()) {
    RCLCPP_ERROR(
      rclcpp::get_logger("MecanumPicoHardware"),
      "Cannot activate — serial port not connected.");
    return hardware_interface::CallbackReturn::ERROR;
  }
  comms_.send_empty_msg();  // Wake up the Pico
  if (diagnostics_) {
    diagnostics_->set_connected(comms_.connected());
  }

  // Fresh orientation estimate per activation — the filter re-initializes
  // roll/pitch from the first trustworthy gravity sample in read() and then
  // recalibrates the gyro bias: the robot must stand still for ~1 s after
  // activation (kCalibSamples standstill samples) before yaw integration
  // starts.
  imu_filter_.reset();
  imu_orientation_ = {0.0, 0.0, 0.0, 1.0};
  imu_calib_logged_ = false;
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Successfully activated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// =============================================================================
// on_deactivate — stop motors, leave port open
// =============================================================================
hardware_interface::CallbackReturn MecanumPicoHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Deactivating...");
  if (comms_.connected()) {
    // Send zero command to all motors before deactivating
    comms_.set_motor_values(0, 0, 0, 0);
  }
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"), "Successfully deactivated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

// =============================================================================
// read — request encoder ticks; update pos and vel for all 4 wheels
// =============================================================================
hardware_interface::return_type MecanumPicoHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  if (diagnostics_) {
    diagnostics_->set_connected(comms_.connected());
  }
  if (!comms_.connected()) {
    return hardware_interface::return_type::ERROR;
  }
  if (diagnostics_) {
    diagnostics_->note_read_cycle();
  }

  int fl_enc = 0, fr_enc = 0, rl_enc = 0, rr_enc = 0;
  const bool encoder_ok = comms_.read_encoder_values(fl_enc, fr_enc, rl_enc, rr_enc);
  if (diagnostics_) {
    diagnostics_->note_encoder_read(encoder_ok);
  }
  if (!encoder_ok) {
    RCLCPP_ERROR(
      rclcpp::get_logger("MecanumPicoHardware"),
      "Failed to read encoder values from Pico.");
    return hardware_interface::return_type::ERROR;
  }

  const double dt = period.seconds();

  // Lambda: update position and velocity for one wheel
  auto update_wheel = [&](Wheel & w, int new_enc) {
      const double prev_pos = w.pos;
      w.enc = new_enc;
      w.pos = w.calc_enc_angle();
      w.vel = (dt > 0.0) ? ((w.pos - prev_pos) / dt) : 0.0;
    };

  update_wheel(wheel_fl_, fl_enc);
  update_wheel(wheel_fr_, fr_enc);
  update_wheel(wheel_rl_, rl_enc);
  update_wheel(wheel_rr_, rr_enc);

  // --- IMU (accel + gyro), only if a <sensor> block was found in on_init ---
  if (has_imu_sensor_) {
    double ax_g = 0.0, ay_g = 0.0, az_g = 0.0;
    double gx_dps = 0.0, gy_dps = 0.0, gz_dps = 0.0;

    const bool imu_ok = comms_.read_imu_values(ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps);
    if (diagnostics_) {
      diagnostics_->note_imu_read(imu_ok);
    }
    if (imu_ok) {
      constexpr double kGravity = 9.80665;        // [g]     -> [m/s^2]
      constexpr double kDegToRad = M_PI / 180.0;  // [deg/s] -> [rad/s]

      imu_data_[0] = ax_g * kGravity;
      imu_data_[1] = ay_g * kGravity;
      imu_data_[2] = az_g * kGravity;
      imu_data_[3] = gx_dps * kDegToRad;
      imu_data_[4] = gy_dps * kDegToRad;
      imu_data_[5] = gz_dps * kDegToRad;

      // Fuse into an orientation quaternion (complementary filter) — the
      // imu_sensor_broadcaster requires orientation.x/y/z/w to activate.
      if (has_orientation_) {
        imu_filter_.update(
          imu_data_[0], imu_data_[1], imu_data_[2],
          imu_data_[3], imu_data_[4], imu_data_[5],
          period.seconds());
        imu_filter_.quaternion(
          imu_orientation_[0], imu_orientation_[1],
          imu_orientation_[2], imu_orientation_[3]);
        if (imu_filter_.calibrated() && !imu_calib_logged_) {
          imu_calib_logged_ = true;
          RCLCPP_INFO(
            rclcpp::get_logger("MecanumPicoHardware"),
            "Gyro bias calibrated after standstill: [%.5f, %.5f, %.5f] rad/s",
            imu_filter_.bias_x(), imu_filter_.bias_y(), imu_filter_.bias_z());
        }
      }
    } else {
      // Non-fatal: keep the last known IMU values and continue. The wheel
      // odometry (the safety-critical path) must not be blocked by a flaky
      // IMU read on the same serial link.
      // ALT: unthrottled RCLCPP_WARN — bei 100 Hz read() flutete das Log
      static rclcpp::Clock steady_clock(RCL_STEADY_TIME);
      RCLCPP_WARN_THROTTLE(
        rclcpp::get_logger("MecanumPicoHardware"), steady_clock, 5000,
        "Failed to read IMU values from Pico — keeping last known values.");
    }
  }

  return hardware_interface::return_type::OK;
}

// =============================================================================
// write — convert rad/s commands to ticks-per-loop; send to Pico
// =============================================================================
hardware_interface::return_type MecanumPicoHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (diagnostics_) {
    diagnostics_->set_connected(comms_.connected());
  }
  if (!comms_.connected()) {
    return hardware_interface::return_type::ERROR;
  }

  // Convert rad/s → ticks-per-loop
  // ticks_per_s = rad/s / rads_per_count
  // ticks_per_loop = ticks_per_s / loop_rate
  auto to_ticks_per_loop = [&](const Wheel & w) -> int {
      if (w.rads_per_count <= 0.0) {return 0;}
      const double ticks_per_s = w.cmd / w.rads_per_count;
      return static_cast<int>(ticks_per_s / cfg_.loop_rate);
    };

  comms_.set_motor_values(
    to_ticks_per_loop(wheel_fl_),
    to_ticks_per_loop(wheel_fr_),
    to_ticks_per_loop(wheel_rl_),
    to_ticks_per_loop(wheel_rr_)
  );

  // ALT: // MIGRATION SPRINT 5: float velocity commands (rad/s)
  // ALT: comms_.set_motor_values(
  // ALT:   wheel_fl_.cmd,
  // ALT:   wheel_fr_.cmd,
  // ALT:   wheel_rl_.cmd,
  // ALT:   wheel_rr_.cmd
  // ALT: );

  return hardware_interface::return_type::OK;
}

}  // namespace mecanum_pico

// ---------------------------------------------------------------------------
// Plugin export — must be last
// ---------------------------------------------------------------------------
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  mecanum_pico::MecanumPicoHardware,
  hardware_interface::SystemInterface)
