// MIGRATION STATUS: COMPLETE
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Single-wheel data structure — completely wheel-count-agnostic.
// Instantiate once per physical wheel (4 times for mecanum drive).

#ifndef MECANUM_PICO__WHEEL_HPP_
#define MECANUM_PICO__WHEEL_HPP_

#include <string>
#include <cmath>

/**
 * @brief Represents one wheel's state and command.
 *
 * Fields:
 *  - name  : joint name as declared in the URDF (e.g. "front_left_wheel_joint")
 *  - enc   : raw encoder tick count (cumulative, signed 32-bit integer)
 *  - cmd   : velocity command from the controller [rad/s]
 *  - pos   : current angular position derived from encoder [rad]
 *  - vel   : current angular velocity derived from encoder differentiation [rad/s]
 *  - rads_per_count : conversion factor = (2*PI) / enc_counts_per_rev
 */
class Wheel
{
public:
  /// Joint name matching the URDF declaration.
  std::string name = "";

  /// Cumulative encoder tick count (updated every read() cycle).
  int enc = 0;

  /// Velocity command received from the controller [rad/s].
  double cmd = 0.0;

  /// Integrated angular position from encoder [rad].
  double pos = 0.0;

  /// Angular velocity computed by differentiation over dt [rad/s].
  double vel = 0.0;

  /// Pre-computed radians per encoder tick = (2*PI) / enc_counts_per_rev.
  double rads_per_count = 0.0;

  Wheel() = default;

  /**
   * @brief Construct and immediately configure the wheel.
   * @param wheel_name     Joint name (must match URDF).
   * @param counts_per_rev Encoder resolution [ticks/revolution].
   */
  Wheel(const std::string & wheel_name, int counts_per_rev)
  {
    setup(wheel_name, counts_per_rev);
  }

  /**
   * @brief (Re-)configure name and encoder resolution.
   */
  void setup(const std::string & wheel_name, int counts_per_rev)
  {
    name = wheel_name;
    rads_per_count = (2.0 * M_PI) / counts_per_rev;
  }

  /**
   * @brief Compute angular position from cumulative encoder ticks.
   * @return Angle in radians.
   */
  double calc_enc_angle() const
  {
    return enc * rads_per_count;
  }
};

#endif  // MECANUM_PICO__WHEEL_HPP_
