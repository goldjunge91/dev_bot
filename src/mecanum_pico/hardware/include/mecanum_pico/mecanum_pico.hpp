// MIGRATION STATUS: IN PROGRESS (Sprint 1 data model complete; Sprint 2 comms complete)
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// MecanumPicoHardware — ros2_control SystemInterface for a 4-wheel mecanum robot
// driven by a Raspberry Pi Pico over USB-CDC serial.

#ifndef MECANUM_PICO__MECANUM_PICO_HPP_
#define MECANUM_PICO__MECANUM_PICO_HPP_

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
  struct Config {
    /// Joint names — must match the URDF joint declarations exactly.
    std::string front_left_wheel_name  = "front_left_wheel_joint";
    std::string front_right_wheel_name = "front_right_wheel_joint";
    std::string rear_left_wheel_name   = "rear_left_wheel_joint";
    std::string rear_right_wheel_name  = "rear_right_wheel_joint";

    float       loop_rate          = 30.0f;  ///< Controller update rate [Hz]
    std::string device             = "/dev/ttyACM0";  ///< Serial device path
    int         baud_rate          = 115200;
    int         timeout_ms         = 1000;
    int         enc_counts_per_rev = 1440;  ///< Encoder resolution [ticks/rev] — MEASURE YOUR ROBOT
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
  Config    cfg_;    ///< Parameters loaded from URDF hardware parameters

  // Four independent mecanum wheels.
  Wheel wheel_fl_;  ///< Front-left  wheel — positive cmd = forward-left contribution
  Wheel wheel_fr_;  ///< Front-right wheel — positive cmd = forward-right contribution
  Wheel wheel_rl_;  ///< Rear-left   wheel — positive cmd = backward-left contribution
  Wheel wheel_rr_;  ///< Rear-right  wheel — positive cmd = backward-right contribution
};

}  // namespace mecanum_pico

#endif  // MECANUM_PICO__MECANUM_PICO_HPP_
