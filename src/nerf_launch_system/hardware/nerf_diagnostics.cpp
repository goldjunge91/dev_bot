/**
 * @file nerf_diagnostics.cpp
 * @brief Implementierung von NerfDiagnostics (siehe Header für Design-Notizen)
 */
#include "nerf_launch_system/nerf_diagnostics.hpp"

namespace nerf_launch_system {

NerfDiagnostics::NerfDiagnostics(const std::string &hardware_name,
                                 const std::string &device,
                                 int baud_rate,
                                 double expected_rate_hz) :
    hardware_name_(hardware_name),
    device_(device),
    baud_rate_(baud_rate),
    expected_rate_hz_(expected_rate_hz) {
    // Fixed node name: this hardware component is a singleton per robot, and
    // hardware component names (info_.name) are not guaranteed to be valid
    // ROS node names (they may contain characters ROS node names forbid).
    node_ = std::make_shared<rclcpp::Node>("nerf_launch_system_diagnostics");

    updater_ = std::make_unique<diagnostic_updater::Updater>(node_, 1.0);
    updater_->setHardwareID(hardware_name_);
    updater_->add("Nerf Serial Connection", this, &NerfDiagnostics::connection_task);
    updater_->add("Control Loop Rate", this, &NerfDiagnostics::loop_rate_task);
}

NerfDiagnostics::~NerfDiagnostics() {
    stop();
}

void NerfDiagnostics::start() {
    if (running_.exchange(true)) {
        return;  // already running
    }
    last_check_time_ = std::chrono::steady_clock::now();
    last_read_count_snapshot_ = read_count_.load(std::memory_order_relaxed);
    executor_.add_node(node_);
    spin_thread_ = std::thread([this]() { executor_.spin(); });
}

void NerfDiagnostics::stop() {
    if (!running_.exchange(false)) {
        return;  // already stopped (or never started)
    }
    executor_.cancel();
    if (spin_thread_.joinable()) {
        spin_thread_.join();
    }
    executor_.remove_node(node_);
}

void NerfDiagnostics::set_connected(bool connected) {
    connected_.store(connected, std::memory_order_relaxed);
}

void NerfDiagnostics::set_armed(bool armed) {
    armed_.store(armed, std::memory_order_relaxed);
}

void NerfDiagnostics::note_write_failure() {
    write_failures_.fetch_add(1, std::memory_order_relaxed);
}

void NerfDiagnostics::note_read_cycle() {
    read_count_.fetch_add(1, std::memory_order_relaxed);
}

void NerfDiagnostics::connection_task(diagnostic_updater::DiagnosticStatusWrapper &stat) {
    const bool connected = connected_.load(std::memory_order_relaxed);
    const bool armed = armed_.load(std::memory_order_relaxed);
    const uint64_t write_fail = write_failures_.load(std::memory_order_relaxed);

    if (!connected) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::ERROR,
                     "Serial port to Nerf launcher is not open");
    } else if (write_fail > 0) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::WARN,
                     "At least one serial write has failed since startup");
    } else {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::OK, "Connected");
    }

    stat.add("device", device_);
    stat.add("baud_rate", baud_rate_);
    stat.add("armed", armed);
    stat.add("write_failures_total", write_fail);
}

void NerfDiagnostics::loop_rate_task(diagnostic_updater::DiagnosticStatusWrapper &stat) {
    const auto now = std::chrono::steady_clock::now();
    const uint64_t count_now = read_count_.load(std::memory_order_relaxed);

    const double elapsed_s = std::chrono::duration<double>(now - last_check_time_).count();
    const uint64_t delta = count_now - last_read_count_snapshot_;
    const double achieved_hz = (elapsed_s > 0.0) ? (static_cast<double>(delta) / elapsed_s) : 0.0;

    last_check_time_ = now;
    last_read_count_snapshot_ = count_now;

    // Warn below 50% of the expected rate (the controller_manager's
    // update_rate) — a hint that the control loop is stalling, not just
    // normal jitter.
    const double min_acceptable_hz = 0.5 * expected_rate_hz_;

    if (achieved_hz < min_acceptable_hz) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::WARN,
                     "read() rate below 50% of the expected control-loop rate");
    } else {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::OK, "Rate OK");
    }

    stat.add("expected_rate_hz", expected_rate_hz_);
    stat.add("achieved_rate_hz", achieved_hz);
}

}  // namespace nerf_launch_system
