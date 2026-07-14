/**
 * @file test_nerf_diagnostics.cpp
 * @brief Unit tests for NerfDiagnostics.
 *
 * Only exercises connection_task()/loop_rate_task() directly (no executor
 * spinning, no real serial port) — the same "call the public task method
 * directly" pattern mecanum_pico's HardwareDiagnostics tests use.
 */
#include <gtest/gtest.h>

#include "diagnostic_updater/diagnostic_updater.hpp"
#include "nerf_launch_system/nerf_diagnostics.hpp"
#include "rclcpp/rclcpp.hpp"

class NerfDiagnosticsTest : public ::testing::Test {
protected:
    static void SetUpTestSuite() { rclcpp::init(0, nullptr); }
    static void TearDownTestSuite() { rclcpp::shutdown(); }
};

TEST_F(NerfDiagnosticsTest, ReportsOkWhenConnectedAndNoFailures) {
    nerf_launch_system::NerfDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 100.0);
    diag.set_connected(true);

    diagnostic_updater::DiagnosticStatusWrapper stat;
    diag.connection_task(stat);

    EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::OK);
}

TEST_F(NerfDiagnosticsTest, ReportsErrorWhenDisconnected) {
    nerf_launch_system::NerfDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 100.0);
    diag.set_connected(false);

    diagnostic_updater::DiagnosticStatusWrapper stat;
    diag.connection_task(stat);

    EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::ERROR);
}

TEST_F(NerfDiagnosticsTest, WarnsAfterWriteFailure) {
    nerf_launch_system::NerfDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 100.0);
    diag.set_connected(true);
    diag.note_write_failure();

    diagnostic_updater::DiagnosticStatusWrapper stat;
    diag.connection_task(stat);

    EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::WARN);
}

TEST_F(NerfDiagnosticsTest, ArmedStateIsReportedInConnectionTask) {
    nerf_launch_system::NerfDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 100.0);
    diag.set_connected(true);
    diag.set_armed(true);

    diagnostic_updater::DiagnosticStatusWrapper stat;
    diag.connection_task(stat);

    // DiagnosticStatusWrapper has an add<bool>() specialization that
    // stringifies to "True"/"False" (see diagnostic_status_wrapper.hpp).
    bool found = false;
    std::string armed_value;
    for (const auto &kv : stat.values) {
        if (kv.key == "armed") {
            found = true;
            armed_value = kv.value;
        }
    }
    EXPECT_TRUE(found);
    EXPECT_EQ(armed_value, "True");
}

TEST_F(NerfDiagnosticsTest, LoopRateTaskWarnsWithNoReadCycles) {
    nerf_launch_system::NerfDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 100.0);

    // No note_read_cycle() calls at all -> achieved rate is 0 Hz, well below
    // 50% of the expected 100 Hz rate.
    diagnostic_updater::DiagnosticStatusWrapper stat;
    diag.loop_rate_task(stat);

    EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::WARN);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
