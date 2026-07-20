// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0

#include "mecanum_pico/hardware_diagnostics.hpp"

namespace mecanum_pico {

HardwareDiagnostics::HardwareDiagnostics(const std::string &hardware_name,
                                         const std::string &device,
                                         int baud_rate,
                                         double loop_rate_hz) :
    hardware_name_(hardware_name),
    device_(device),
    baud_rate_(baud_rate),
    loop_rate_hz_(loop_rate_hz) {
    // Fixed node name: this hardware component is a singleton per robot, and
    // hardware component names (info_.name) are not guaranteed to be valid
    // ROS node names (they may contain characters ROS node names forbid).
    node_ = std::make_shared<rclcpp::Node>("mecanum_pico_diagnostics");

    updater_ = std::make_unique<diagnostic_updater::Updater>(node_, 1.0);
    updater_->setHardwareID(hardware_name_);
    updater_->add("Pico Serial Connection", this, &HardwareDiagnostics::connection_task);
    updater_->add("Control Loop Rate", this, &HardwareDiagnostics::loop_rate_task);
}

HardwareDiagnostics::~HardwareDiagnostics() {
    stop();
}

void HardwareDiagnostics::start() {
    if (running_.exchange(true)) {
        return;  // already running
    }
    last_check_time_ = std::chrono::steady_clock::now();
    last_read_count_snapshot_ = read_count_.load(std::memory_order_relaxed);
    executor_.add_node(node_);
    spin_thread_ = std::thread([this]() { executor_.spin(); });
}

void HardwareDiagnostics::stop() {
    if (!running_.exchange(false)) {
        return;  // already stopped (or never started)
    }
    executor_.cancel();
    if (spin_thread_.joinable()) {
        spin_thread_.join();
    }
    executor_.remove_node(node_);
}

void HardwareDiagnostics::set_connected(bool connected) {
    connected_.store(connected, std::memory_order_relaxed);
}

void HardwareDiagnostics::note_encoder_read(bool success) {
    if (!success) {
        encoder_read_failures_.fetch_add(1, std::memory_order_relaxed);
    }
}

void HardwareDiagnostics::note_imu_read(bool success) {
    if (!success) {
        imu_read_failures_.fetch_add(1, std::memory_order_relaxed);
    }
}

void HardwareDiagnostics::note_read_cycle() {
    read_count_.fetch_add(1, std::memory_order_relaxed);
}

void HardwareDiagnostics::connection_task(diagnostic_updater::DiagnosticStatusWrapper &stat) {
    const bool connected = connected_.load(std::memory_order_relaxed);
    const uint64_t enc_fail = encoder_read_failures_.load(std::memory_order_relaxed);
    const uint64_t imu_fail = imu_read_failures_.load(std::memory_order_relaxed);

    if (!connected) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::ERROR,
                     "Serial port to Pico is not open");
    } else if (enc_fail > 0) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::WARN,
                     "Encoder read(s) have timed out at least once since startup");
    } else {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::OK, "Connected");
    }

    stat.add("device", device_);
    stat.add("baud_rate", baud_rate_);
    stat.add("encoder_read_failures_total", enc_fail);
    stat.add("imu_read_failures_total", imu_fail);
}

void HardwareDiagnostics::loop_rate_task(diagnostic_updater::DiagnosticStatusWrapper &stat) {
    const auto now = std::chrono::steady_clock::now();
    const uint64_t count_now = read_count_.load(std::memory_order_relaxed);

    const double elapsed_s = std::chrono::duration<double>(now - last_check_time_).count();
    const uint64_t delta = count_now - last_read_count_snapshot_;
    const double achieved_hz = (elapsed_s > 0.0) ? (static_cast<double>(delta) / elapsed_s) : 0.0;

    last_check_time_ = now;
    last_read_count_snapshot_ = count_now;

    // Warn below 50% of the configured loop_rate — a hint that the control
    // loop or the serial link is stalling, not just normal jitter.
    const double min_acceptable_hz = 0.5 * loop_rate_hz_;

    if (achieved_hz < min_acceptable_hz) {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::WARN,
                     "read() rate below 50% of configured loop_rate");
    } else {
        stat.summary(diagnostic_msgs::msg::DiagnosticStatus::OK, "Rate OK");
    }

    stat.add("configured_loop_rate_hz", loop_rate_hz_);
    stat.add("achieved_rate_hz", achieved_hz);
}

}  // namespace mecanum_pico
