// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// HardwareDiagnostics — /diagnostics reporting for the Pico serial link.
//
// hardware_interface::SystemInterface has no rclcpp::Node of its own on
// this ROS 2 distribution (Humble) — see hardware_interface/system_interface.hpp.
// diagnostic_updater::Updater needs a node (it creates a wall timer and a
// publisher on it), so this class owns a small internal node + a dedicated
// single-threaded executor purely to host the Updater. That executor is
// spun on its own background thread — never on the ros2_control read()/
// write() thread — so it can never block the control loop.
//
// Producer side (set_connected / note_*) is called from read()/write()
// (the ros2_control update thread) and only ever touches std::atomic
// members: no locks, no allocation, safe to call from that thread.
// Consumer side (connection_task / loop_rate_task) runs on the internal
// diagnostics thread via the Updater's own timer. Both task methods are
// public and take a plain DiagnosticStatusWrapper so they can also be
// unit-tested directly, without spinning any executor — the same pattern
// PicoComms uses for parse_encoder_response/parse_imu_response.

#ifndef MECANUM_PICO__HARDWARE_DIAGNOSTICS_HPP_
#define MECANUM_PICO__HARDWARE_DIAGNOSTICS_HPP_

#include <atomic>
#include <chrono>
#include <memory>
#include <string>
#include <thread>

#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_updater/diagnostic_updater.hpp"
#include "rclcpp/rclcpp.hpp"

namespace mecanum_pico
{

class HardwareDiagnostics
{
public:
  /**
   * @param hardware_name Reported as the diagnostic_updater hardware_id
   *                       (free-form — not used as a ROS node/topic name).
   * @param device         Serial device path, reported for context.
   * @param baud_rate      Serial baud rate, reported for context.
   * @param loop_rate_hz   Configured control-loop rate — used as the
   *                       reference for the "Control Loop Rate" check.
   */
  HardwareDiagnostics(
    const std::string & hardware_name,
    const std::string & device,
    int baud_rate,
    double loop_rate_hz);

  ~HardwareDiagnostics();

  HardwareDiagnostics(const HardwareDiagnostics &) = delete;
  HardwareDiagnostics & operator=(const HardwareDiagnostics &) = delete;

  /// Starts the internal node + executor thread. Call from on_configure().
  void start();

  /// Stops and joins the executor thread. Call from on_cleanup(). Safe to
  /// call even if start() was never called, or twice in a row.
  void stop();

  // ---------------------------------------------------------------------
  // Producer side — call from read()/write() (the ros2_control RT-ish
  // update thread). Lock-free: only touches std::atomic members.
  // ---------------------------------------------------------------------

  /// Reflects the current comms_.connected() state.
  void set_connected(bool connected);

  /// Call once per read() with the result of reading the encoders.
  void note_encoder_read(bool success);

  /// Call once per read() with the result of reading the IMU (if present).
  void note_imu_read(bool success);

  /// Call once per read() invocation, regardless of success/failure —
  /// used to measure the achieved control-loop rate.
  void note_read_cycle();

  // ---------------------------------------------------------------------
  // Diagnostic tasks — public for unit-testability (see class comment).
  // Normally only invoked by the internal diagnostic_updater::Updater.
  // ---------------------------------------------------------------------
  void connection_task(diagnostic_updater::DiagnosticStatusWrapper & stat);
  void loop_rate_task(diagnostic_updater::DiagnosticStatusWrapper & stat);

private:
  std::string hardware_name_;
  std::string device_;
  int baud_rate_;
  double loop_rate_hz_;

  std::atomic<bool> connected_{false};
  std::atomic<uint64_t> encoder_read_failures_{0};
  std::atomic<uint64_t> imu_read_failures_{0};
  std::atomic<uint64_t> read_count_{0};

  // Diagnostics-thread-only bookkeeping for loop_rate_task — only ever
  // touched from the thread that calls loop_rate_task (the internal
  // diagnostics executor, or a test calling it directly/single-threaded).
  uint64_t last_read_count_snapshot_{0};
  std::chrono::steady_clock::time_point last_check_time_{std::chrono::steady_clock::now()};

  rclcpp::Node::SharedPtr node_;
  std::unique_ptr<diagnostic_updater::Updater> updater_;
  rclcpp::executors::SingleThreadedExecutor executor_;
  std::thread spin_thread_;
  std::atomic<bool> running_{false};
};

}  // namespace mecanum_pico

#endif  // MECANUM_PICO__HARDWARE_DIAGNOSTICS_HPP_
