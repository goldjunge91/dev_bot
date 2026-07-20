// MIGRATION STATUS: COMPLETE (Sprint 1 — Wheel data model tests)
// Sprint 1 TDD tests for the Wheel struct.
// These tests must pass with zero hardware connected.

#include "mecanum_pico/wheel.hpp"

#include <cmath>
#include <gtest/gtest.h>

// Define PI locally to avoid relying on M_PI macro
static const double PI = std::acos(-1.0);

// ---------------------------------------------------------------------------
// WheelTest — basic construction and field access
// ---------------------------------------------------------------------------

TEST(WheelTest, DefaultConstruction) {
    Wheel w;
    EXPECT_EQ(w.name, "");
    EXPECT_EQ(w.enc, 0);
    EXPECT_DOUBLE_EQ(w.cmd, 0.0);
    EXPECT_DOUBLE_EQ(w.pos, 0.0);
    EXPECT_DOUBLE_EQ(w.vel, 0.0);
    EXPECT_DOUBLE_EQ(w.rads_per_count, 0.0);
}

TEST(WheelTest, NameIsSetOnConstruction) {
    Wheel w("front_left_wheel_joint", 20);
    EXPECT_EQ(w.name, "front_left_wheel_joint");
}

TEST(WheelTest, RadsPerCountCalculatedCorrectly) {
    Wheel w("test_wheel", 20);
    EXPECT_NEAR(w.rads_per_count, (2.0 * PI) / 20.0, 1e-12);
}

TEST(WheelTest, CalcEncAngleCorrect) {
    Wheel w("test", 20);  // 20 ticks per revolution
    w.enc = 10;
    // 10 / 20 * 2*PI = PI
    EXPECT_NEAR(w.calc_enc_angle(), PI, 1e-9);
}

TEST(WheelTest, CalcEncAngleZeroWhenEncZero) {
    Wheel w("test", 1440);
    w.enc = 0;
    EXPECT_DOUBLE_EQ(w.calc_enc_angle(), 0.0);
}

TEST(WheelTest, CalcEncAngleNegativeTicks) {
    Wheel w("test", 20);
    w.enc = -10;
    EXPECT_NEAR(w.calc_enc_angle(), -PI, 1e-9);
}

TEST(WheelTest, SetupOverridesName) {
    Wheel w("old_name", 20);
    w.setup("new_name", 40);
    EXPECT_EQ(w.name, "new_name");
    EXPECT_NEAR(w.rads_per_count, (2.0 * PI) / 40.0, 1e-12);
}

// ---------------------------------------------------------------------------
// FourWheelTest — 4 wheels are fully independent
// ---------------------------------------------------------------------------

TEST(FourWheelTest, WheelsAreIndependent) {
    Wheel fl("fl", 20), fr("fr", 20), rl("rl", 20), rr("rr", 20);
    fl.cmd = 1.0;
    fr.cmd = 2.0;
    rl.cmd = 3.0;
    rr.cmd = 4.0;

    EXPECT_DOUBLE_EQ(fl.cmd, 1.0);
    EXPECT_DOUBLE_EQ(fr.cmd, 2.0);
    EXPECT_DOUBLE_EQ(rl.cmd, 3.0);
    EXPECT_DOUBLE_EQ(rr.cmd, 4.0);
}

TEST(FourWheelTest, WheelNamesAreUnique) {
    Wheel fl("front_left_wheel_joint", 1440);
    Wheel fr("front_right_wheel_joint", 1440);
    Wheel rl("rear_left_wheel_joint", 1440);
    Wheel rr("rear_right_wheel_joint", 1440);

    EXPECT_NE(fl.name, fr.name);
    EXPECT_NE(fl.name, rl.name);
    EXPECT_NE(fl.name, rr.name);
    EXPECT_NE(fr.name, rl.name);
    EXPECT_NE(fr.name, rr.name);
    EXPECT_NE(rl.name, rr.name);
}

TEST(FourWheelTest, EncoderUpdatesAreIndependent) {
    Wheel fl("fl", 1440), fr("fr", 1440), rl("rl", 1440), rr("rr", 1440);
    fl.enc = 100;
    fr.enc = 200;
    rl.enc = 300;
    rr.enc = 400;

    EXPECT_EQ(fl.enc, 100);
    EXPECT_EQ(fr.enc, 200);
    EXPECT_EQ(rl.enc, 300);
    EXPECT_EQ(rr.enc, 400);
}

// main is provided by test/test_main.cpp
