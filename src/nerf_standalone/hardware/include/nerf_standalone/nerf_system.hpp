#ifndef NERF_STANDALONE_NERF_SYSTEM_HPP
#define NERF_STANDALONE_NERF_SYSTEM_HPP

#include <memory>
#include <string>
#include <vector>

#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include <libserial/SerialPort.h>

namespace nerf_standalone {
struct NerfJoints {
  double trigger_pos = 0.0;
  double pusher_vel = 0.0;
  double flywheel_l_vel = 0.0;
  double flywheel_r_vel = 0.0;
  double arming_pos = 0.0;
};

struct NerfJointStates {
  double trigger_pos = 0.0;
  double trigger_vel = 0.0;
  double pusher_pos = 0.0;
  double pusher_vel = 0.0;
  double flywheel_l_pos = 0.0;
  double flywheel_l_vel = 0.0;
  double flywheel_r_pos = 0.0;
  double flywheel_r_vel = 0.0;
  double arming_pos = 0.0;
  double arming_vel = 0.0;
};

class NerfComms {
public:
  NerfComms() = default;
  void connect(const std::string &serial_device, int32_t baud_rate);
  void disconnect();
  bool connected() const;
  void send_command(const std::string &cmd);

private:
  LibSerial::SerialPort serial_conn_;
};

class NerfSystem : public hardware_interface::SystemInterface {
public:
  using SharedPtr = std::shared_ptr<NerfSystem>;
  using ConstSharedPtr = std::shared_ptr<const NerfSystem>;

  // LifecycleNodeInterface
  hardware_interface::CallbackReturn
  on_init(const hardware_interface::HardwareInfo &info) override;

  hardware_interface::CallbackReturn
  on_configure(const rclcpp_lifecycle::State &previous_state) override;

  hardware_interface::CallbackReturn
  on_cleanup(const rclcpp_lifecycle::State &previous_state) override;

  hardware_interface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State &previous_state) override;

  hardware_interface::CallbackReturn
  on_deactivate(const rclcpp_lifecycle::State &previous_state) override;

  // SystemInterface
  hardware_interface::return_type read(const rclcpp::Time &time,
                                       const rclcpp::Duration &period) override;

  hardware_interface::return_type
  write(const rclcpp::Time &time, const rclcpp::Duration &period) override;

  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override;

private:
  NerfComms comms_;
  NerfJoints hw_commands_;
  NerfJointStates hw_states_; // Optional, if we had feedback

  // Config
  std::string port_;
  int baud_rate_;

  // Mappings
  double tilt_min_rad_ = 5.23;
  double tilt_max_rad_ = 6.28;

  double *get_state_ptr(const std::string &joint_name,
                         const std::string &interface_name);
  double *get_command_ptr(const std::string &joint_name,
                           const std::string &interface_name);
};

} // namespace nerf_standalone

#endif // NERF_STANDALONE_NERF_SYSTEM_HPP
