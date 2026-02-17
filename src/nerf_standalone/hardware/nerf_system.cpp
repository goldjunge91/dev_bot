#include "nerf_standalone/nerf_system.hpp"
#include "rclcpp/logging.hpp"

#include <cmath>
#include <sstream>
#include <vector>

#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace nerf_standalone {

// --- NerfComms Implementation ---

void NerfComms::connect(const std::string &serial_device, int32_t baud_rate) {
  // Convert baud rate
  LibSerial::BaudRate baud;
  switch (baud_rate) {
  case 9600:
    baud = LibSerial::BaudRate::BAUD_9600;
    break;
  case 57600:
    baud = LibSerial::BaudRate::BAUD_57600;
    break;
  case 115200:
    baud = LibSerial::BaudRate::BAUD_115200;
    break;
  default:
    baud = LibSerial::BaudRate::BAUD_115200;
    break;
  }

  serial_conn_.Open(serial_device);
  serial_conn_.SetBaudRate(baud);
  serial_conn_.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
  serial_conn_.SetFlowControl(LibSerial::FlowControl::FLOW_CONTROL_NONE);
  serial_conn_.SetParity(LibSerial::Parity::PARITY_NONE);
  serial_conn_.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
}

void NerfComms::disconnect() {
  if (serial_conn_.IsOpen()) {
    try {
      serial_conn_.Close();
    } catch (const std::exception &e) {
      RCLCPP_ERROR(rclcpp::get_logger("NerfComms"),
                   "Error closing serial port: %s", e.what());
    }
  }
}

bool NerfComms::connected() const { return serial_conn_.IsOpen(); }

void NerfComms::send_command(const std::string &cmd) {
  if (!serial_conn_.IsOpen())
    return;

  try {
    // Add newline for Arduino
    serial_conn_.Write(cmd + "\n");
    // serial_conn_.DrainWriteBuffer(); // Optional, ensures sent
  } catch (const std::exception &e) {
    RCLCPP_ERROR(rclcpp::get_logger("NerfComms"),
                 "Serial write failed (%s). Closing port.", e.what());
    disconnect();
  }
}

// --- NerfSystem Implementation ---

hardware_interface::CallbackReturn
NerfSystem::on_init(const hardware_interface::HardwareInfo &info) {
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS) {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Read Parameters
  port_ = info_.hardware_parameters["port"]; // e.g., /dev/ttyACM0
  baud_rate_ = std::stoi(info_.hardware_parameters["baud_rate"]);

  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
              "Initialized NerfSystem on port %s @ %d", port_.c_str(),
              baud_rate_);

  // Verify Joints
  for (const hardware_interface::ComponentInfo &joint : info_.joints) {
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Joint found: %s",
                joint.name.c_str());

    if (joint.name != "trigger_joint" && joint.name != "dart_pusher_joint" &&
        joint.name != "flywheel_left_joint" &&
        joint.name != "flywheel_right_joint" &&
        joint.name != "system_arming_joint") {
      RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"), "Unsupported joint '%s'",
                   joint.name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }

    for (const auto &command_interface : joint.command_interfaces) {
      if (!get_command_ptr(joint.name, command_interface.name)) {
        RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                     "Unsupported command interface '%s' for joint '%s'",
                     command_interface.name.c_str(), joint.name.c_str());
        return hardware_interface::CallbackReturn::ERROR;
      }
    }

    for (const auto &state_interface : joint.state_interfaces) {
      if (!get_state_ptr(joint.name, state_interface.name)) {
        RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                     "Unsupported state interface '%s' for joint '%s'",
                     state_interface.name.c_str(), joint.name.c_str());
        return hardware_interface::CallbackReturn::ERROR;
      }
    }
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface>
NerfSystem::export_state_interfaces() {
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (const auto &joint : info_.joints) {
    for (const auto &interface : joint.state_interfaces) {
      double *state_ptr = get_state_ptr(joint.name, interface.name);
      if (!state_ptr) {
        RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                     "Skipping unsupported state interface '%s' for joint '%s'",
                     interface.name.c_str(), joint.name.c_str());
        continue;
      }
      state_interfaces.emplace_back(hardware_interface::StateInterface(
          joint.name, interface.name, state_ptr));
    }
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface>
NerfSystem::export_command_interfaces() {
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (const auto &joint : info_.joints) {
    for (const auto &interface : joint.command_interfaces) {
      double *command_ptr = get_command_ptr(joint.name, interface.name);
      if (!command_ptr) {
        RCLCPP_ERROR(
            rclcpp::get_logger("NerfSystem"),
            "Skipping unsupported command interface '%s' for joint '%s'",
            interface.name.c_str(), joint.name.c_str());
        continue;
      }
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, interface.name, command_ptr));
    }
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn
NerfSystem::on_configure(const rclcpp_lifecycle::State & /*previous_state*/) {
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
              "Configuring... Opening Serial %s", port_.c_str());
  try {
    comms_.connect(port_, baud_rate_);
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "Serial Connected Successfully");
  } catch (const std::exception &e) {
    RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                 "Failed to open serial port: %s", e.what());
    return hardware_interface::CallbackReturn::ERROR;
  }
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
NerfSystem::on_cleanup(const rclcpp_lifecycle::State & /*previous_state*/) {
  comms_.disconnect();
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
NerfSystem::on_activate(const rclcpp_lifecycle::State & /*previous_state*/) {
  // No auto-arm on activate
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
              "System Activated (Waiting for ARM command)");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
NerfSystem::on_deactivate(const rclcpp_lifecycle::State & /*previous_state*/) {
  // Safety stop and DISARM
  comms_.send_command("TEST_ESC 0");
  comms_.send_command("DISARM");
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System DISARMED");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type
NerfSystem::read(const rclcpp::Time & /*time*/,
                 const rclcpp::Duration & /*period*/) {
  // Open-loop feedback: mirror commands into state values.
  // Guard against NaN/Inf coming from controllers by sanitizing values.
  auto safe_copy = [](double src, double &dst) {
    if (std::isfinite(src)) {
      dst = src;
    } else {
      // on invalid input, keep previous dst (or set to 0.0 if uninitialized)
      dst = dst; // preserve previous value
    }
  };

  safe_copy(hw_commands_.trigger_pos, hw_states_.trigger_pos);
  hw_states_.trigger_vel = 0.0;
  safe_copy(hw_commands_.pusher_vel, hw_states_.pusher_vel);
  safe_copy(hw_commands_.flywheel_l_vel, hw_states_.flywheel_l_vel);
  safe_copy(hw_commands_.flywheel_r_vel, hw_states_.flywheel_r_vel);
  safe_copy(hw_commands_.arming_pos, hw_states_.arming_pos);

  // Final safety: ensure no state contains NaN/Inf before publishing
  auto sanitize = [](double &v) {
    if (!std::isfinite(v))
      v = 0.0;
  };
  sanitize(hw_states_.trigger_pos);
  sanitize(hw_states_.trigger_vel);
  sanitize(hw_states_.pusher_pos);
  sanitize(hw_states_.pusher_vel);
  sanitize(hw_states_.flywheel_l_pos);
  sanitize(hw_states_.flywheel_l_vel);
  sanitize(hw_states_.flywheel_r_pos);
  sanitize(hw_states_.flywheel_r_vel);
  sanitize(hw_states_.arming_pos);
  sanitize(hw_states_.arming_vel);
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type
NerfSystem::write(const rclcpp::Time & /*time*/,
                  const rclcpp::Duration & /*period*/) {
  if (!comms_.connected()) {
    static bool warned = false;
    if (!warned) {
      RCLCPP_WARN(rclcpp::get_logger("NerfSystem"),
                  "Serial disconnected. Skipping write commands.");
      warned = true;
    }
    return hardware_interface::return_type::OK;
  }

  // 0. Manual Arming (Position > 0.5 -> ARM)
  static bool armed = false;
  bool should_arm = (hw_commands_.arming_pos > 0.5);

  if (should_arm && !armed) {
    comms_.send_command("ARM");
    armed = true;
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: ARM");
  } else if (!should_arm && armed) {
    comms_.send_command("DISARM");
    armed = false;
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: DISARM");
  }

  if (!armed)
    return hardware_interface::return_type::OK;

  // 1. Tilt (Trigger Joint) Logic
  // REVISED: Use UP/DN commands for continuous rotation/winch servo
  // instead of absolute T_POS.
  double target_pos = hw_commands_.trigger_pos;
  double current_pos = hw_states_.trigger_pos;
  double delta = target_pos - current_pos;

  // Only act if there is a significant change request
  // We assume the upstream controller holds the value when not moving
  if (std::abs(delta) > 0.01) {
    // Calculate duration based on delta magnitude?
    // For now, use a fixed burst for the "step" sent by teleop
    // Teleop step is 0.05 rad.
    // Firmware command: UP <ms>

    // Empirically: 0.05 rad -> ~50-100ms?
    // Let's try 100ms per step.
    int duration = 100;

    // Rate limiting to prevent flooding serial?
    // The loop runs at 30Hz-50Hz.
    // We update the state immediately so we don't re-send the same delta.

    std::stringstream ss;
    if (delta > 0) {
      ss << "UP " << duration;
    } else {
      ss << "DN " << duration;
    }
    comms_.send_command(ss.str());

    // Update feedback to match target immediately (Open Loop)
    hw_states_.trigger_pos = target_pos;
  }

  // 2. Pusher (Velocity)
  // Logic: If velocity > threshold, trigger a single shot or burst
  // The firmware command "TEST_SHOT <ms>" pulses the pusher.
  static bool pusher_active = false;
  if (hw_commands_.pusher_vel > 1.0 && !pusher_active) {
    // Fire one shot (pusher cycle)
    // We use TEST_SHOT which runs the pusher for N ms
    comms_.send_command("TEST_SHOT 500");
    pusher_active = true;
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: TEST_SHOT");
  } else if (hw_commands_.pusher_vel < 0.1) {
    pusher_active = false;
  }

  // 3. Flywheels (Velocity)
  // Map rad/s to 0-100% power
  // Max speed ~100 rad/s?
  double max_vel = 100.0;
  // Use average of both wheels for single ESC command
  double avg_vel = (std::abs(hw_commands_.flywheel_l_vel) +
                    std::abs(hw_commands_.flywheel_r_vel)) /
                   2.0;

  int pwm_percent = static_cast<int>((avg_vel / max_vel) * 100);
  pwm_percent = std::max(0, std::min(100, pwm_percent));

  static int last_pwm = -1;
  if (pwm_percent == 0 && last_pwm != 0) {
    // Explicitly send PWM 1000 (Min Throttle) to stop
    // This bypasses the firmware bug where TEST_ESC 0 sets 20% power.
    comms_.send_command("PWM 1000");
    last_pwm = 0;
  } else if (std::abs(pwm_percent - last_pwm) > 2) {
    // Deadband to reduce traffic
    std::stringstream ss;
    ss << "TEST_ESC " << pwm_percent;
    comms_.send_command(ss.str());
    last_pwm = pwm_percent;
  }

  return hardware_interface::return_type::OK;
}

double *NerfSystem::get_state_ptr(const std::string &joint_name,
                                  const std::string &interface_name) {
  if (interface_name == hardware_interface::HW_IF_POSITION) {
    if (joint_name == "trigger_joint") {
      return &hw_states_.trigger_pos;
    }
    if (joint_name == "dart_pusher_joint") {
      return &hw_states_.pusher_pos;
    }
    if (joint_name == "flywheel_left_joint") {
      return &hw_states_.flywheel_l_pos;
    }
    if (joint_name == "flywheel_right_joint") {
      return &hw_states_.flywheel_r_pos;
    }
    if (joint_name == "system_arming_joint") {
      return &hw_states_.arming_pos;
    }
  }

  if (interface_name == hardware_interface::HW_IF_VELOCITY) {
    if (joint_name == "trigger_joint") {
      return &hw_states_.trigger_vel;
    }
    if (joint_name == "dart_pusher_joint") {
      return &hw_states_.pusher_vel;
    }
    if (joint_name == "flywheel_left_joint") {
      return &hw_states_.flywheel_l_vel;
    }
    if (joint_name == "flywheel_right_joint") {
      return &hw_states_.flywheel_r_vel;
    }
    if (joint_name == "system_arming_joint") {
      return &hw_states_.arming_vel;
    }
  }

  return nullptr;
}

double *NerfSystem::get_command_ptr(const std::string &joint_name,
                                    const std::string &interface_name) {
  if (joint_name == "trigger_joint" &&
      interface_name == hardware_interface::HW_IF_POSITION) {
    return &hw_commands_.trigger_pos;
  }

  if (joint_name == "dart_pusher_joint" &&
      interface_name == hardware_interface::HW_IF_VELOCITY) {
    return &hw_commands_.pusher_vel;
  }

  if (joint_name == "flywheel_left_joint" &&
      interface_name == hardware_interface::HW_IF_VELOCITY) {
    return &hw_commands_.flywheel_l_vel;
  }

  if (joint_name == "flywheel_right_joint" &&
      interface_name == hardware_interface::HW_IF_VELOCITY) {
    return &hw_commands_.flywheel_r_vel;
  }

  if (joint_name == "system_arming_joint" &&
      interface_name == hardware_interface::HW_IF_POSITION) {
    return &hw_commands_.arming_pos;
  }

  return nullptr;
}

} // namespace nerf_standalone

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(nerf_standalone::NerfSystem,
                       hardware_interface::SystemInterface)
