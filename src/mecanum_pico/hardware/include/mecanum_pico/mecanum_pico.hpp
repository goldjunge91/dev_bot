// MIGRATION STATUS: IN PROGRESS (Sprint 1 data model complete; Sprint 2 comms complete)
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// MecanumPicoHardware — ros2_control SystemInterface for a 4-wheel mecanum robot
// driven by a Raspberry Pi Pico over USB-CDC serial.

#ifndef MECANUM_PICO__MECANUM_PICO_HPP_
#define MECANUM_PICO__MECANUM_PICO_HPP_

#include "mecanum_pico/hardware_diagnostics.hpp"
#include "mecanum_pico/imu_fusion.hpp"
#include "mecanum_pico/pico_comms.hpp"
#include "mecanum_pico/visibility_control.h"
#include "mecanum_pico/wheel.hpp"

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/clock.hpp"
#include "rclcpp/duration.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp/time.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include <array>
#include <memory>
#include <string>
#include <vector>

namespace mecanum_pico
{

class MecanumPicoHardware : public hardware_interface::SystemInterface
{
public:
  // -------------------------------------------------------------------------
  // Hardware parameters loaded from URDF / ros2_control.xacro
  // -------------------------------------------------------------------------
  struct Config
  {
    /// Joint names — must match the URDF joint declarations exactly.
    std::string front_left_wheel_name = "front_left_wheel_joint";
    std::string front_right_wheel_name = "front_right_wheel_joint";
    std::string rear_left_wheel_name = "rear_left_wheel_joint";
    std::string rear_right_wheel_name = "rear_right_wheel_joint";

    float loop_rate = 30.0f;                 ///< Controller update rate [Hz]
    std::string device = "/dev/ttyACM0";              ///< Serial device path
    int baud_rate = 115200;
    int timeout_ms = 1000;
    int enc_counts_per_rev = 1440;          ///< Encoder resolution [ticks/rev] — MEASURE YOUR ROBOT
  };

  RCLCPP_SHARED_PTR_DEFINITIONS(MecanumPicoHardware)

  // -------------------------------------------------------------------------
  // Lifecycle callbacks (ros2_control)
  // -------------------------------------------------------------------------

  MECANUM_PICO_PUBLIC
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  MECANUM_PICO_PUBLIC
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  MECANUM_PICO_PUBLIC
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  MECANUM_PICO_PUBLIC
  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  MECANUM_PICO_PUBLIC
  hardware_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & previous_state) override;

  MECANUM_PICO_PUBLIC
  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  MECANUM_PICO_PUBLIC
  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  MECANUM_PICO_PUBLIC
  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  MECANUM_PICO_PUBLIC
  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  PicoComms comms_;  ///< USB-CDC serial communication to the Pico
  Config cfg_;       ///< Parameters loaded from URDF hardware parameters

  // Four independent mecanum wheels.
  Wheel wheel_fl_;  ///< Front-left  wheel — positive cmd = forward-left contribution
  Wheel wheel_fr_;  ///< Front-right wheel — positive cmd = forward-right contribution
  Wheel wheel_rl_;  ///< Rear-left   wheel — positive cmd = backward-left contribution
  Wheel wheel_rr_;  ///< Rear-right  wheel — positive cmd = backward-right contribution

  // -------------------------------------------------------------------------
  // IMU sensor (ICM-20948, read via Pico 'i' command)
  // -------------------------------------------------------------------------
  /// Sensor name — must match the URDF <sensor name="..."> declaration.
  /// Populated from info_.sensors[0].name in on_init() if a sensor is declared,
  /// otherwise falls back to "imu_sensor".
  std::string imu_sensor_name_ = "imu_sensor";

  /// Order: [0]=linear_acceleration.x [1]=.y [2]=.z
  ///        [3]=angular_velocity.x    [4]=.y [5]=.z
  /// Units: SI (m/s^2, rad/s) — converted from firmware units (g, deg/s) in read().
  std::array<double, 6> imu_data_{};

  /// Orientation quaternion [x, y, z, w] computed by imu_filter_ in read().
  /// Exported as orientation.x/y/z/w state interfaces when the URDF declares
  /// them (has_orientation_). The Humble imu_sensor_broadcaster requires
  /// these to activate — the raw ICM-20948 does not measure orientation.
  std::array<double, 4> imu_orientation_{0.0, 0.0, 0.0, 1.0};

  /// Complementary filter fusing gyro+accel into imu_orientation_ (RT-safe).
  ImuComplementaryFilter imu_filter_;

  /// Edge flag for the one-time "gyro bias calibrated" log in read().
  bool imu_calib_logged_ = false;

  /// True once a sensor block was found in the URDF — export_state_interfaces()
  /// only advertises the IMU interfaces when this is true.
  bool has_imu_sensor_ = false;

  /// True when the URDF sensor block declares the 4 orientation interfaces
  /// (10-interface layout) in addition to accel+gyro (6-interface layout).
  bool has_orientation_ = false;

  // -------------------------------------------------------------------------
  // /diagnostics reporting (Pico serial connection + control-loop rate).
  // Created in on_configure(), started/stopped alongside the serial
  // connection lifecycle. See hardware_diagnostics.hpp for why this owns
  // its own node/thread instead of using a node this class doesn't have.
  // -------------------------------------------------------------------------
  std::unique_ptr<HardwareDiagnostics> diagnostics_;
};

}  // namespace mecanum_pico

#endif  // MECANUM_PICO__MECANUM_PICO_HPP_
