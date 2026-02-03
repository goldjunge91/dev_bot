#include "nerf_standalone/nerf_system.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <sstream>
#include <vector>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

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
    serial_conn_.Close();
  }
}

bool NerfComms::connected() const { return serial_conn_.IsOpen(); }

void NerfComms::send_command(const std::string &cmd) {
  if (!serial_conn_.IsOpen())
    return;

  // Add newline for Arduino
  serial_conn_.Write(cmd + "\n");
  // serial_conn_.DrainWriteBuffer(); // Optional, ensures sent
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
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface>
NerfSystem::export_state_interfaces() {
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (const auto &joint : info_.joints) {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
        joint.name, hardware_interface::HW_IF_POSITION,
        &hw_states_.trigger_pos));

    // Add velocity too just in case controllers ask for it
    state_interfaces.emplace_back(hardware_interface::StateInterface(
        joint.name, hardware_interface::HW_IF_VELOCITY,
        &hw_states_.flywheel_l_vel));
    // Note: mapping same var to all for now as dummy feedback
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface>
NerfSystem::export_command_interfaces() {
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (const auto &joint : info_.joints) {
    if (joint.name == "trigger_joint") {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, hardware_interface::HW_IF_POSITION,
          &hw_commands_.trigger_pos));
    } else if (joint.name == "dart_pusher_joint") {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, hardware_interface::HW_IF_VELOCITY,
          &hw_commands_.pusher_vel));
    } else if (joint.name == "flywheel_left_joint") {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, hardware_interface::HW_IF_VELOCITY,
          &hw_commands_.flywheel_l_vel));
    } else if (joint.name == "flywheel_right_joint") {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, hardware_interface::HW_IF_VELOCITY,
          &hw_commands_.flywheel_r_vel));
    } else if (joint.name == "system_arming_joint") {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          joint.name, hardware_interface::HW_IF_POSITION,
          &hw_commands_.arming_pos));
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
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type
NerfSystem::write(const rclcpp::Time & /*time*/,
                  const rclcpp::Duration & /*period*/) {
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

  // 1. Trigger (Position) - Not used in new firmware protocol via Serial for
  // now, or could map to TILT if needed. Firmware has UP/DN. Leaving blank to
  // avoid safety issues or complexity for now.

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
  if (std::abs(pwm_percent - last_pwm) > 2) { // Deadband to reduce traffic
    std::stringstream ss;
    ss << "TEST_ESC " << pwm_percent;
    comms_.send_command(ss.str());
    last_pwm = pwm_percent;
  }

  return hardware_interface::return_type::OK;
}

} // namespace nerf_standalone

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(nerf_standalone::NerfSystem,
                       hardware_interface::SystemInterface)
