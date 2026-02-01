#include "nerf_standalone/nerf_system.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <vector>
#include <sstream>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace nerf_standalone
{

// --- NerfComms Implementation ---

void NerfComms::connect(const std::string &serial_device, int32_t baud_rate)
{
    // Convert baud rate
    LibSerial::BaudRate baud;
    switch(baud_rate) {
        case 9600: baud = LibSerial::BaudRate::BAUD_9600; break;
        case 57600: baud = LibSerial::BaudRate::BAUD_57600; break;
        case 115200: baud = LibSerial::BaudRate::BAUD_115200; break;
        default: baud = LibSerial::BaudRate::BAUD_115200; break;
    }

    serial_conn_.Open(serial_device);
    serial_conn_.SetBaudRate(baud);
    serial_conn_.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serial_conn_.SetFlowControl(LibSerial::FlowControl::FLOW_CONTROL_NONE);
    serial_conn_.SetParity(LibSerial::Parity::PARITY_NONE);
    serial_conn_.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
}

void NerfComms::disconnect()
{
    if (serial_conn_.IsOpen()) {
        serial_conn_.Close();
    }
}

bool NerfComms::connected() const
{
    return serial_conn_.IsOpen();
}

void NerfComms::send_command(const std::string &cmd)
{
    if (!serial_conn_.IsOpen()) return;
    
    // Add newline for Arduino
    serial_conn_.Write(cmd + "\n");
    // serial_conn_.DrainWriteBuffer(); // Optional, ensures sent
}

// --- NerfSystem Implementation ---

hardware_interface::CallbackReturn NerfSystem::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (
    hardware_interface::SystemInterface::on_init(info) !=
    hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Read Parameters
  port_ = info_.hardware_parameters["port"]; // e.g., /dev/ttyACM0
  baud_rate_ = std::stoi(info_.hardware_parameters["baud_rate"]);
  
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Initialized NerfSystem on port %s @ %d", port_.c_str(), baud_rate_);

  // Verify Joints
  for (const hardware_interface::ComponentInfo & joint : info_.joints)
  {
      RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Joint found: %s", joint.name.c_str());
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> NerfSystem::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (const auto & joint : info_.joints)
  {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint.name, hardware_interface::HW_IF_POSITION, &hw_states_.trigger_pos));
    
    // Add velocity too just in case controllers ask for it
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint.name, hardware_interface::HW_IF_VELOCITY, &hw_states_.flywheel_l_vel)); 
      // Note: mapping same var to all for now as dummy feedback
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> NerfSystem::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (const auto & joint : info_.joints)
  {
    if (joint.name == "trigger_joint") {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(
            joint.name, hardware_interface::HW_IF_POSITION, &hw_commands_.trigger_pos));
    } else if (joint.name == "dart_pusher_joint") {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(
            joint.name, hardware_interface::HW_IF_VELOCITY, &hw_commands_.pusher_vel));
    } else if (joint.name == "flywheel_left_joint") {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(
            joint.name, hardware_interface::HW_IF_VELOCITY, &hw_commands_.flywheel_l_vel));
    } else if (joint.name == "flywheel_right_joint") {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(
            joint.name, hardware_interface::HW_IF_VELOCITY, &hw_commands_.flywheel_r_vel));
    } else if (joint.name == "system_arming_joint") {
        command_interfaces.emplace_back(hardware_interface::CommandInterface(
            joint.name, hardware_interface::HW_IF_POSITION, &hw_commands_.arming_pos));
    }
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn NerfSystem::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Configuring... Opening Serial %s", port_.c_str());
  try {
      comms_.connect(port_, baud_rate_);
      RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Serial Connected Successfully");
  } catch (const std::exception &e) {
      RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"), "Failed to open serial port: %s", e.what());
      return hardware_interface::CallbackReturn::ERROR;
  }
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_cleanup(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  comms_.disconnect();
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  // No auto-arm on activate
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System Activated (Waiting for ARM command)");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  // Safety stop and DISARM
  comms_.send_command("f 0 0");
  comms_.send_command("d");
  RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System DISARMED");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type NerfSystem::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type NerfSystem::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // 0. Manual Arming (Position > 0.5 -> ARM)
  static bool armed = false;
  bool should_arm = (hw_commands_.arming_pos > 0.5);
  
  if (should_arm && !armed) {
      comms_.send_command("a");
      armed = true;
      RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: ARM");
  } else if (!should_arm && armed) {
      comms_.send_command("d");
      armed = false;
      RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: DISARM");
  }

  // 1. Trigger (Position)
  // Map rad (5.23 - 6.28) to degrees (0 - 180 or limited range)
  // 6.28 (Up) -> 90? 5.23 (Down) -> 0?
  // Let's assume input is calibrated 0-1 normalized logic in Node, 
  // but here we receive raw joint limits.
  // URDF: 5.23 to 6.28.
  const double tilt_min_rad_ = 5.23;
  const double tilt_max_rad_ = 6.28;
  
  double trigger_ratio = (hw_commands_.trigger_pos - tilt_min_rad_) / (tilt_max_rad_ - tilt_min_rad_);
  trigger_ratio = std::max(0.0, std::min(1.0, trigger_ratio)); // Clamp
  
  // Assuming servo 0-180 covers the range. 
  // Adjust '180' if mechanical limits differ. 
  int trigger_angle = static_cast<int>(trigger_ratio * 180); 
  
  std::stringstream ss_t;
  ss_t << "t " << trigger_angle;
  comms_.send_command(ss_t.str());

  // 2. Pusher (Velocity)
  // Continuous servo: 90=stop, 0=full reverse, 180=full fwd
  // Or mapped: 0=stop, 100=max speed
  // Let's assume input velocity > 0 means PUSH.
  int pusher_val = 90;
  if (hw_commands_.pusher_vel > 0.1) pusher_val = 180; // Full fwd
  else if (hw_commands_.pusher_vel < -0.1) pusher_val = 0; // Reverse?
  
  // Custom logic: if we just want simple "go", input 10.0 -> 180
  if (hw_commands_.pusher_vel > 1.0) pusher_val = 160; 
  if (hw_commands_.pusher_vel == 0.0) pusher_val = 90;

  std::stringstream ss_p;
  ss_p << "p " << pusher_val;
  comms_.send_command(ss_p.str());

  // 3. Flywheels (Velocity)
  // Map velocity (rad/s?) to PWM (0-255)
  // Max speed ~100 rad/s?
  double max_vel = 100.0;
  int pwm_l = static_cast<int>((hw_commands_.flywheel_l_vel / max_vel) * 255);
  int pwm_r = static_cast<int>((hw_commands_.flywheel_r_vel / max_vel) * 255);
  
  std::stringstream ss_f;
  ss_f << "f " << std::abs(pwm_l) << " " << std::abs(pwm_r);
  comms_.send_command(ss_f.str());

  return hardware_interface::return_type::OK;
}

}  // namespace nerf_standalone

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  nerf_standalone::NerfSystem, hardware_interface::SystemInterface)
