/**
 * @file nerf_diagnostics.hpp
 * @brief /diagnostics reporting for the Nerf launcher's serial link.
 *
 * hardware_interface::SystemInterface has no rclcpp::Node of its own on
 * this ROS 2 distribution (Humble), but diagnostic_updater::Updater needs
 * one (it creates a wall timer and a /diagnostics publisher on it). This
 * class therefore owns a small internal node + a dedicated single-threaded
 * executor purely to host the Updater, spun on its own background thread —
 * never on the ros2_control read()/write() thread, so it can never block
 * the control loop. Same pattern as mecanum_pico's HardwareDiagnostics.
 *
 * Producer side (set_* / note_*) is called from read()/write() (the
 * ros2_control update thread) and only ever touches std::atomic members:
 * no locks, no allocation, safe to call from that thread. Consumer side
 * (connection_task / loop_rate_task) runs on the internal diagnostics
 * thread via the Updater's own timer. Both task methods are public so
 * they can also be unit-tested directly, without spinning any executor.
 */
#ifndef NERF_LAUNCH_SYSTEM_NERF_DIAGNOSTICS_HPP
#define NERF_LAUNCH_SYSTEM_NERF_DIAGNOSTICS_HPP

#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_updater/diagnostic_updater.hpp"
#include "rclcpp/rclcpp.hpp"

#include <atomic>
#include <chrono>
#include <memory>
#include <string>
#include <thread>

namespace nerf_launch_system {

class NerfDiagnostics {
public:
    /**
     * @param hardware_name  Reported as the diagnostic_updater hardware_id
     *                       (free-form — not used as a ROS node/topic name).
     * @param device         Serial device path, reported for context.
     * @param baud_rate      Serial baud rate, reported for context.
     * @param expected_rate_hz Reference rate for the "Control Loop Rate"
     *                       check (the controller_manager's update_rate —
     *                       this hardware component has no rate of its own).
     */
    NerfDiagnostics(const std::string &hardware_name,
                    const std::string &device,
                    int baud_rate,
                    double expected_rate_hz);

    ~NerfDiagnostics();

    NerfDiagnostics(const NerfDiagnostics &) = delete;
    NerfDiagnostics &operator=(const NerfDiagnostics &) = delete;

    /// Starts the internal node + executor thread. Call from on_configure().
    void start();

    /// Stops and joins the executor thread. Call from on_cleanup(). Safe to
    /// call even if start() was never called, or twice in a row.
    void stop();

    // ---------------------------------------------------------------------
    // Producer side — call from read()/write() (the ros2_control update
    // thread). Lock-free: only touches std::atomic members.
    // ---------------------------------------------------------------------

    /// Reflects the current comms_.connected() state.
    void set_connected(bool connected);

    /// Reflects the current armed_ state — a Nerf launcher being armed is
    /// itself safety-relevant, worth surfacing on /diagnostics.
    void set_armed(bool armed);

    /// Call whenever a send_command() is immediately followed by the
    /// serial link dropping (NerfCommunication::send_command() disconnects
    /// internally on a write exception) — i.e. once per detected failure.
    void note_write_failure();

    /// Call once per read() invocation — used to measure the achieved
    /// control-loop rate.
    void note_read_cycle();

    // ---------------------------------------------------------------------
    // Diagnostic tasks — public for unit-testability (see class comment).
    // Normally only invoked by the internal diagnostic_updater::Updater.
    // ---------------------------------------------------------------------
    void connection_task(diagnostic_updater::DiagnosticStatusWrapper &stat);
    void loop_rate_task(diagnostic_updater::DiagnosticStatusWrapper &stat);

private:
    std::string hardware_name_;
    std::string device_;
    int baud_rate_;
    double expected_rate_hz_;

    std::atomic<bool> connected_{false};
    std::atomic<bool> armed_{false};
    std::atomic<uint64_t> write_failures_{0};
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

}  // namespace nerf_launch_system

#endif  // NERF_LAUNCH_SYSTEM_NERF_DIAGNOSTICS_HPP
