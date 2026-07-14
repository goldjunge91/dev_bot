// Copyright 2026 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Complementary filter: fuses gyro + accel into an orientation quaternion.
// Pure C++, no ROS dependencies, no allocation — safe to call from the
// real-time read() path and trivially unit-testable (like wheel.hpp).

#ifndef MECANUM_PICO__IMU_FUSION_HPP_
#define MECANUM_PICO__IMU_FUSION_HPP_

#include <cmath>

namespace mecanum_pico
{

/**
 * @brief Complementary filter producing an orientation quaternion from
 *        6-DoF IMU data (no magnetometer).
 *
 * Why this exists: the ICM-20948 on the Pico only measures angular velocity
 * and linear acceleration. The Humble imu_sensor_broadcaster however requires
 * orientation.x/y/z/w state interfaces to activate — orientation has to be
 * COMPUTED somewhere. Doing it here keeps sim (Gazebo computes orientation)
 * and real hardware exporting identical interfaces.
 *
 * Behaviour:
 *  - roll/pitch: gyro integration, continuously corrected towards the
 *    accelerometer gravity vector (complementary blend, kAlpha) — but only
 *    while the accel magnitude is plausibly ~1 g (robot not accelerating hard).
 *  - yaw: pure gyro integration. Drifts slowly without a magnetometer; the
 *    EKF consumes yaw with imu0_relative: true, so slow drift is acceptable.
 *  - dt guards: dt <= 0 or dt > kMaxDt skips integration for that sample.
 *  - gyro bias: the first kCalibSamples standstill samples after reset() are
 *    averaged into a per-axis bias that is subtracted from all later gyro
 *    readings (MEMS zero-rate offset would otherwise integrate into yaw
 *    drift). The robot must sit still ~1 s after activation; samples taken
 *    while accelerating merely extend the calibration window.
 */
class ImuComplementaryFilter
{
public:
  /// Blend factor: fraction of the gyro-integrated angle kept per update
  /// (the remaining 1 - kAlpha pulls towards the accel gravity reference).
  static constexpr double kAlpha = 0.98;

  /// Samples with dt above this are treated as gaps (no integration).
  static constexpr double kMaxDt = 0.5;

  /// Accel magnitude window around 1 g in which the gravity reference is
  /// trusted for roll/pitch correction.
  static constexpr double kGravity = 9.80665;
  static constexpr double kAccelTrustLow = 0.7 * kGravity;
  static constexpr double kAccelTrustHigh = 1.3 * kGravity;

  /// Standstill samples averaged into the gyro bias after reset()
  /// (~1 s at the controller_manager's 100 Hz update rate).
  static constexpr int kCalibSamples = 100;

  /**
   * @brief Feed one IMU sample.
   * @param ax,ay,az  linear acceleration [m/s^2] (gravity included)
   * @param gx,gy,gz  angular velocity [rad/s]
   * @param dt        time since the previous sample [s]
   */
  void update(
    double ax, double ay, double az,
    double gx, double gy, double gz,
    double dt)
  {
    if (!std::isfinite(ax) || !std::isfinite(ay) || !std::isfinite(az) ||
      !std::isfinite(gx) || !std::isfinite(gy) || !std::isfinite(gz) ||
      !std::isfinite(dt))
    {
      return;
    }

    const double accel_norm = std::sqrt(ax * ax + ay * ay + az * az);
    const bool accel_trusted =
      accel_norm > kAccelTrustLow && accel_norm < kAccelTrustHigh;

    if (!initialized_) {
      // First usable sample: take roll/pitch straight from gravity.
      if (accel_trusted) {
        roll_ = std::atan2(ay, az);
        pitch_ = std::atan2(-ax, std::sqrt(ay * ay + az * az));
        yaw_ = 0.0;
        initialized_ = true;
      }
      return;
    }

    if (dt <= 0.0 || dt > kMaxDt) {
      return;  // clock jump / gap — skip integration for this sample
    }

    // Gyro bias calibration: average the first kCalibSamples standstill
    // samples. Only samples with a trusted accel magnitude count (~1 g —
    // hard acceleration means the gyro is not at rest either); untrusted
    // samples merely extend the window instead of corrupting the mean.
    // No gyro integration during this phase: roll/pitch keep tracking
    // gravity, yaw stays 0 — the robot is standing still anyway.
    if (!calibrated_) {
      if (accel_trusted) {
        bias_sum_x_ += gx;
        bias_sum_y_ += gy;
        bias_sum_z_ += gz;
        ++calib_count_;
        roll_ = std::atan2(ay, az);
        pitch_ = std::atan2(-ax, std::sqrt(ay * ay + az * az));
        if (calib_count_ >= kCalibSamples) {
          bias_x_ = bias_sum_x_ / calib_count_;
          bias_y_ = bias_sum_y_ / calib_count_;
          bias_z_ = bias_sum_z_ / calib_count_;
          calibrated_ = true;
        }
      }
      return;
    }

    gx -= bias_x_;
    gy -= bias_y_;
    gz -= bias_z_;

    // Gyro integration.
    double roll_gyro = roll_ + gx * dt;
    double pitch_gyro = pitch_ + gy * dt;
    yaw_ = wrap_angle(yaw_ + gz * dt);

    // Accel correction for roll/pitch (only when the gravity vector is
    // trustworthy — i.e. the robot is not accelerating hard).
    if (accel_trusted) {
      const double roll_acc = std::atan2(ay, az);
      const double pitch_acc = std::atan2(-ax, std::sqrt(ay * ay + az * az));
      roll_ = kAlpha * roll_gyro + (1.0 - kAlpha) * roll_acc;
      pitch_ = kAlpha * pitch_gyro + (1.0 - kAlpha) * pitch_acc;
    } else {
      roll_ = roll_gyro;
      pitch_ = pitch_gyro;
    }
  }

  /**
   * @brief Current orientation as a normalized quaternion (x, y, z, w).
   *        Identity until the filter has initialized from a first sample.
   */
  void quaternion(double & qx, double & qy, double & qz, double & qw) const
  {
    const double cr = std::cos(roll_ * 0.5), sr = std::sin(roll_ * 0.5);
    const double cp = std::cos(pitch_ * 0.5), sp = std::sin(pitch_ * 0.5);
    const double cy = std::cos(yaw_ * 0.5), sy = std::sin(yaw_ * 0.5);

    qw = cr * cp * cy + sr * sp * sy;
    qx = sr * cp * cy - cr * sp * sy;
    qy = cr * sp * cy + sr * cp * sy;
    qz = cr * cp * sy - sr * sp * cy;

    // Guard against numeric drift — keep the quaternion normalized.
    const double norm = std::sqrt(qx * qx + qy * qy + qz * qz + qw * qw);
    if (norm > 0.0) {
      qx /= norm;
      qy /= norm;
      qz /= norm;
      qw /= norm;
    } else {
      qx = qy = qz = 0.0;
      qw = 1.0;
    }
  }

  /// Reset to identity / uninitialized (call from on_configure/on_activate).
  /// Also restarts the gyro bias calibration — every activation recalibrates.
  void reset()
  {
    roll_ = pitch_ = yaw_ = 0.0;
    initialized_ = false;
    bias_x_ = bias_y_ = bias_z_ = 0.0;
    bias_sum_x_ = bias_sum_y_ = bias_sum_z_ = 0.0;
    calib_count_ = 0;
    calibrated_ = false;
  }

  double roll() const {return roll_;}
  double pitch() const {return pitch_;}
  double yaw() const {return yaw_;}
  bool initialized() const {return initialized_;}
  bool calibrated() const {return calibrated_;}
  double bias_x() const {return bias_x_;}
  double bias_y() const {return bias_y_;}
  double bias_z() const {return bias_z_;}

private:
  static double wrap_angle(double a)
  {
    while (a > M_PI) {a -= 2.0 * M_PI;}
    while (a < -M_PI) {a += 2.0 * M_PI;}
    return a;
  }

  double roll_ = 0.0;   ///< [rad]
  double pitch_ = 0.0;  ///< [rad]
  double yaw_ = 0.0;    ///< [rad]
  bool initialized_ = false;

  // Gyro zero-rate bias [rad/s], learned during the calibration phase.
  double bias_x_ = 0.0;
  double bias_y_ = 0.0;
  double bias_z_ = 0.0;
  double bias_sum_x_ = 0.0;
  double bias_sum_y_ = 0.0;
  double bias_sum_z_ = 0.0;
  int calib_count_ = 0;
  bool calibrated_ = false;
};

}  // namespace mecanum_pico

#endif  // MECANUM_PICO__IMU_FUSION_HPP_
