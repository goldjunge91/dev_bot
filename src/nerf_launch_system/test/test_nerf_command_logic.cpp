/**
 * @file test_nerf_command_logic.cpp
 * @brief Unit tests for the pure Nerf command-generation functions.
 *
 * No ROS/serial dependency — exercises make_tilt_command()/make_shot_command()
 * directly. TiltRegression* is the regression test for the read()/write()
 * mirroring bug: read() must not mirror hw_commands_.tilt_pos into
 * hw_states_.tilt_pos, otherwise delta collapses to ~0 and no UP/DN command
 * is ever produced. These tests simulate the write()-side integration loop
 * in isolation (feeding new_tilt_pos back in as current_pos, the way
 * NerfSystem::write() does) to prove the sequence actually converges.
 */
#include "nerf_launch_system/nerf_command_logic.hpp"

#include <gtest/gtest.h>

using nerf_launch_system::make_shot_command;
using nerf_launch_system::make_tilt_command;

namespace {
constexpr double kTiltMin = -0.52;
constexpr double kTiltMax = 0.52;
}  // namespace

// --- make_tilt_command ---

TEST(MakeTiltCommand, NoCommandWithinDeadband) {
    auto step = make_tilt_command(0.1, 0.1005, kTiltMin, kTiltMax);
    EXPECT_FALSE(step.has_value());
}

TEST(MakeTiltCommand, MovesUpTowardHigherTarget) {
    auto step = make_tilt_command(0.5, 0.0, kTiltMin, kTiltMax);
    ASSERT_TRUE(step.has_value());
    EXPECT_EQ(step->command, "UP 100");
    EXPECT_DOUBLE_EQ(step->new_tilt_pos, 0.05);
}

TEST(MakeTiltCommand, MovesDownTowardLowerTarget) {
    auto step = make_tilt_command(-0.5, 0.0, kTiltMin, kTiltMax);
    ASSERT_TRUE(step.has_value());
    EXPECT_EQ(step->command, "DN 100");
    EXPECT_DOUBLE_EQ(step->new_tilt_pos, -0.05);
}

TEST(MakeTiltCommand, StepDoesNotOvershootTarget) {
    // Nur noch 0.02 rad bis zum Ziel — der 0.05-Schritt darf nicht überschießen.
    auto step = make_tilt_command(0.5, 0.48, kTiltMin, kTiltMax);
    ASSERT_TRUE(step.has_value());
    EXPECT_DOUBLE_EQ(step->new_tilt_pos, 0.5);
}

TEST(MakeTiltCommand, ClampsOutOfRangeTarget) {
    // Alte Servo-Rohwerte (z. B. 6.28) müssen auf tilt_max geclampt werden,
    // nicht endlos gegen die mechanische Grenze weiterlaufen.
    auto step = make_tilt_command(6.28, 0.0, kTiltMin, kTiltMax);
    ASSERT_TRUE(step.has_value());
    EXPECT_EQ(step->command, "UP 100");
    EXPECT_LE(step->new_tilt_pos, kTiltMax);
}

TEST(MakeTiltCommand, RegressionConvergesToTargetOverMultipleCalls) {
    // Simuliert den write()-Integrationsloop: new_tilt_pos wird als
    // current_pos in den nächsten Aufruf zurückgespeist (wie
    // NerfSystem::write() es jetzt tut). Vor dem A1-Fix hätte ein
    // read()-Mirror hier dafür gesorgt, dass current_pos == target sofort
    // nach dem ersten Schritt wäre und niemals ein zweiter UP/DN-Befehl
    // nötig würde — dieser Test beweist die tatsächliche Konvergenz über
    // mehrere Zyklen.
    double current = 0.0;
    const double target = 0.5;
    int up_commands = 0;
    int cycles = 0;

    while (cycles < 100) {
        auto step = make_tilt_command(target, current, kTiltMin, kTiltMax);
        if (!step) {
            break;
        }
        EXPECT_EQ(step->command, "UP 100");
        up_commands++;
        current = step->new_tilt_pos;
        cycles++;
    }

    EXPECT_GT(up_commands, 1) << "Tilt sollte über mehrere Zyklen inkrementell konvergieren";
    EXPECT_NEAR(current, target, 0.01);
}

TEST(MakeTiltCommand, RegressionConvergesDownward) {
    double current = 0.3;
    const double target = -0.3;
    int down_commands = 0;
    int cycles = 0;

    while (cycles < 100) {
        auto step = make_tilt_command(target, current, kTiltMin, kTiltMax);
        if (!step) {
            break;
        }
        EXPECT_EQ(step->command, "DN 100");
        down_commands++;
        current = step->new_tilt_pos;
        cycles++;
    }

    EXPECT_GT(down_commands, 1);
    EXPECT_NEAR(current, target, 0.01);
}

// --- make_shot_command ---

TEST(MakeShotCommand, FiresOnceOnPositiveCommand) {
    bool pusher_active = false;
    auto cmd = make_shot_command(10.0, pusher_active);
    ASSERT_TRUE(cmd.has_value());
    EXPECT_EQ(*cmd, "SHOT 10");
    EXPECT_TRUE(pusher_active);
}

TEST(MakeShotCommand, DoesNotRefireWhileCommandStaysPositive) {
    bool pusher_active = false;
    auto first = make_shot_command(10.0, pusher_active);
    ASSERT_TRUE(first.has_value());

    auto second = make_shot_command(10.0, pusher_active);
    EXPECT_FALSE(second.has_value());
    EXPECT_TRUE(pusher_active);
}

TEST(MakeShotCommand, ResetsAndCanFireAgainAfterCommandDrops) {
    bool pusher_active = false;
    make_shot_command(10.0, pusher_active);
    ASSERT_TRUE(pusher_active);

    auto reset_cmd = make_shot_command(0.0, pusher_active);
    EXPECT_FALSE(reset_cmd.has_value());
    EXPECT_FALSE(pusher_active);

    auto refire = make_shot_command(10.0, pusher_active);
    ASSERT_TRUE(refire.has_value());
    EXPECT_EQ(*refire, "SHOT 10");
}

TEST(MakeShotCommand, ZeroOrNegativeCommandNeverFires) {
    bool pusher_active = false;
    EXPECT_FALSE(make_shot_command(0.0, pusher_active).has_value());
    EXPECT_FALSE(make_shot_command(-5.0, pusher_active).has_value());
    EXPECT_FALSE(pusher_active);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
