// MIGRATION STATUS: IN PROGRESS (Sprint 1+2 complete; Sprint 3 URDF wiring pending)
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// MecanumPicoHardware — full ros2_control SystemInterface implementation.
// Handles 4 wheels (front_left, front_right, rear_left, rear_right)
// and communicates with the Raspberry Pi Pico via USB-CDC.
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
  cfg_.front_left_wheel_name  = info_.hardware_parameters.at("front_left_wheel_name");
  cfg_.front_right_wheel_name = info_.hardware_parameters.at("front_right_wheel_name");
  cfg_.rear_left_wheel_name   = info_.hardware_parameters.at("rear_left_wheel_name");
  cfg_.rear_right_wheel_name  = info_.hardware_parameters.at("rear_right_wheel_name");

  cfg_.loop_rate          = std::stof(info_.hardware_parameters.at("loop_rate"));
  cfg_.device             = info_.hardware_parameters.at("device");
  cfg_.baud_rate          = std::stoi(info_.hardware_parameters.at("baud_rate"));
  cfg_.timeout_ms         = std::stoi(info_.hardware_parameters.at("timeout_ms"));
  cfg_.enc_counts_per_rev = std::stoi(info_.hardware_parameters.at("enc_counts_per_rev"));

  // --- Configure wheel data structures -----------------------------------
  wheel_fl_.setup(cfg_.front_left_wheel_name,  cfg_.enc_counts_per_rev);
  wheel_fr_.setup(cfg_.front_right_wheel_name, cfg_.enc_counts_per_rev);
  wheel_rl_.setup(cfg_.rear_left_wheel_name,   cfg_.enc_counts_per_rev);
  wheel_rr_.setup(cfg_.rear_right_wheel_name,  cfg_.enc_counts_per_rev);

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

  // 8 state interfaces total (4 wheels × 2)
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
    RCLCPP_ERROR(rclcpp::get_logger("MecanumPicoHardware"),
                 "Cannot activate — serial port not connected.");
    return hardware_interface::CallbackReturn::ERROR;
  }
  comms_.send_empty_msg();  // Wake up the Pico
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
  if (!comms_.connected()) {
    return hardware_interface::return_type::ERROR;
  }

  int fl_enc = 0, fr_enc = 0, rl_enc = 0, rr_enc = 0;
  if (!comms_.read_encoder_values(fl_enc, fr_enc, rl_enc, rr_enc)) {
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

  return hardware_interface::return_type::OK;
}

// =============================================================================
// write — convert rad/s commands to ticks-per-loop; send to Pico
// =============================================================================
hardware_interface::return_type MecanumPicoHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (!comms_.connected()) {
    return hardware_interface::return_type::ERROR;
  }

  // Convert rad/s → ticks-per-loop
  // ticks_per_s = rad/s / rads_per_count
  // ticks_per_loop = ticks_per_s / loop_rate
  auto to_ticks_per_loop = [&](const Wheel & w) -> int {
    if (w.rads_per_count <= 0.0) { return 0; }
    const double ticks_per_s = w.cmd / w.rads_per_count;
    return static_cast<int>(ticks_per_s / cfg_.loop_rate);
  };

  comms_.set_motor_values(
    to_ticks_per_loop(wheel_fl_),
    to_ticks_per_loop(wheel_fr_),
    to_ticks_per_loop(wheel_rl_),
    to_ticks_per_loop(wheel_rr_)
  );

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
