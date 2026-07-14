// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Unit tests for HardwareDiagnostics. Only exercises connection_task()/
// loop_rate_task() directly (no executor spinning, no real serial port) —
// same "call the public parse/task method directly" pattern PicoComms uses
// for parse_encoder_response/parse_imu_response.

#include <gtest/gtest.h>

#include "diagnostic_updater/diagnostic_updater.hpp"
#include "mecanum_pico/hardware_diagnostics.hpp"
#include "rclcpp/rclcpp.hpp"

class HardwareDiagnosticsTest : public ::testing::Test
{
protected:
  static void SetUpTestSuite() {rclcpp::init(0, nullptr);}
  static void TearDownTestSuite() {rclcpp::shutdown();}
};

TEST_F(HardwareDiagnosticsTest, ReportsOkWhenConnectedAndNoFailures) {
  mecanum_pico::HardwareDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 30.0);
  diag.set_connected(true);

  diagnostic_updater::DiagnosticStatusWrapper stat;
  diag.connection_task(stat);

  EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::OK);
}

TEST_F(HardwareDiagnosticsTest, ReportsErrorWhenDisconnected) {
  mecanum_pico::HardwareDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 30.0);
  diag.set_connected(false);

  diagnostic_updater::DiagnosticStatusWrapper stat;
  diag.connection_task(stat);

  EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::ERROR);
}

TEST_F(HardwareDiagnosticsTest, WarnsAfterEncoderReadFailure) {
  mecanum_pico::HardwareDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 30.0);
  diag.set_connected(true);
  diag.note_encoder_read(false);

  diagnostic_updater::DiagnosticStatusWrapper stat;
  diag.connection_task(stat);

  EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::WARN);
}

TEST_F(HardwareDiagnosticsTest, EncoderSuccessDoesNotIncrementFailureCounter) {
  mecanum_pico::HardwareDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 30.0);
  diag.set_connected(true);
  diag.note_encoder_read(true);
  diag.note_encoder_read(true);

  diagnostic_updater::DiagnosticStatusWrapper stat;
  diag.connection_task(stat);

  EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::OK);
}

TEST_F(HardwareDiagnosticsTest, LoopRateTaskWarnsWithNoReadCycles) {
  mecanum_pico::HardwareDiagnostics diag("test_hw", "/dev/ttyACM0", 115200, 30.0);

  // No note_read_cycle() calls at all -> achieved rate is 0 Hz, well below
  // 50% of the configured 30 Hz loop_rate.
  diagnostic_updater::DiagnosticStatusWrapper stat;
  diag.loop_rate_task(stat);

  EXPECT_EQ(stat.level, diagnostic_msgs::msg::DiagnosticStatus::WARN);
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
