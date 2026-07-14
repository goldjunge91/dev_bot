// Copyright 2026 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Unit tests for the ImuComplementaryFilter (imu_fusion.hpp) — the pure,
// ROS-free gyro+accel fusion that provides the orientation.x/y/z/w state
// interfaces required by the Humble imu_sensor_broadcaster.

#include <gtest/gtest.h>
#include <cmath>
#include "mecanum_pico/imu_fusion.hpp"

using mecanum_pico::ImuComplementaryFilter;

namespace
{
constexpr double kG = ImuComplementaryFilter::kGravity;
constexpr double kDt = 0.01;  // 100 Hz — controller_manager update rate

void expect_normalized(const ImuComplementaryFilter & f)
{
  double qx, qy, qz, qw;
  f.quaternion(qx, qy, qz, qw);
  EXPECT_NEAR(std::sqrt(qx * qx + qy * qy + qz * qz + qw * qw), 1.0, 1e-9);
}
}  // namespace

// Ruhelage: kein Gyro, Accel = reine Gravitation → Identitäts-Quaternion.
TEST(ImuFusionTest, RestingLevelGivesIdentity) {
  ImuComplementaryFilter f;
  for (int i = 0; i < 200; ++i) {
    f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  }
  double qx, qy, qz, qw;
  f.quaternion(qx, qy, qz, qw);
  EXPECT_NEAR(qx, 0.0, 1e-6);
  EXPECT_NEAR(qy, 0.0, 1e-6);
  EXPECT_NEAR(qz, 0.0, 1e-6);
  EXPECT_NEAR(qw, 1.0, 1e-6);
  expect_normalized(f);
}

// Konstante Gyro-Z-Rate: yaw integriert zu rate * t (Ruhelage-Accel).
TEST(ImuFusionTest, GyroZIntegratesYaw) {
  ImuComplementaryFilter f;
  const double rate = 0.5;  // rad/s
  const int steps = 100;    // 1.0 s
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);  // init sample
  for (int i = 0; i < steps; ++i) {
    f.update(0.0, 0.0, kG, 0.0, 0.0, rate, kDt);
  }
  EXPECT_NEAR(f.yaw(), rate * steps * kDt, 1e-6);
  expect_normalized(f);
}

// Accel-Korrektur zieht Roll gegen einen künstlichen Gyro-Drift zurück:
// Gyro meldet konstante Roll-Rate (Drift), Accel bleibt bei "eben" —
// der Komplementäranteil begrenzt den aufgebauten Roll-Fehler.
TEST(ImuFusionTest, AccelCorrectionLimitsGyroDrift) {
  ImuComplementaryFilter f;
  const double drift = 0.05;  // rad/s falscher Gyro-Roll
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  for (int i = 0; i < 1000; ++i) {  // 10 s
    f.update(0.0, 0.0, kG, drift, 0.0, 0.0, kDt);
  }
  // Ohne Korrektur wäre roll = 0.5 rad; der Filter konvergiert gegen den
  // Steady-State-Offset alpha/(1-alpha) * drift * dt ≈ 0.0245 rad.
  EXPECT_LT(std::abs(f.roll()), 0.05);
  expect_normalized(f);
}

// Grober Beschleunigungsstoß (Accel-Magnitude weit weg von 1 g) darf
// Roll/Pitch nicht verfälschen — die Gravity-Korrektur pausiert dann.
TEST(ImuFusionTest, UntrustedAccelDoesNotCorrupt) {
  ImuComplementaryFilter f;
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  const double roll_before = f.roll();
  for (int i = 0; i < 50; ++i) {
    // 3 g seitlich — z. B. Kollision/starkes Anfahren
    f.update(3.0 * kG, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  }
  EXPECT_NEAR(f.roll(), roll_before, 1e-9);
  expect_normalized(f);
}

// dt-Guards: dt=0, negatives dt und absurdes dt erzeugen kein NaN und
// integrieren nicht.
TEST(ImuFusionTest, DtGuardsProduceNoNan) {
  ImuComplementaryFilter f;
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  const double yaw_before = f.yaw();

  f.update(0.0, 0.0, kG, 0.0, 0.0, 1.0, 0.0);    // dt = 0
  f.update(0.0, 0.0, kG, 0.0, 0.0, 1.0, -0.01);  // dt < 0
  f.update(0.0, 0.0, kG, 0.0, 0.0, 1.0, 5.0);    // dt > kMaxDt

  EXPECT_DOUBLE_EQ(f.yaw(), yaw_before);
  EXPECT_TRUE(std::isfinite(f.roll()));
  expect_normalized(f);
}

// NaN-Eingaben werden ignoriert (Serial-Glitch darf den Filter nicht kippen).
TEST(ImuFusionTest, NanInputIsIgnored) {
  ImuComplementaryFilter f;
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  const double nan = std::numeric_limits<double>::quiet_NaN();
  f.update(nan, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  f.update(0.0, 0.0, kG, nan, 0.0, 0.0, kDt);
  EXPECT_TRUE(std::isfinite(f.roll()));
  EXPECT_TRUE(std::isfinite(f.yaw()));
  expect_normalized(f);
}

// reset() bringt den Filter zurück auf Identität/uninitialisiert.
TEST(ImuFusionTest, ResetReturnsToIdentity) {
  ImuComplementaryFilter f;
  f.update(0.0, 0.0, kG, 0.0, 0.0, 0.0, kDt);
  for (int i = 0; i < 100; ++i) {
    f.update(0.0, 0.0, kG, 0.0, 0.0, 1.0, kDt);
  }
  EXPECT_NE(f.yaw(), 0.0);

  f.reset();
  EXPECT_FALSE(f.initialized());
  double qx, qy, qz, qw;
  f.quaternion(qx, qy, qz, qw);
  EXPECT_DOUBLE_EQ(qw, 1.0);
  EXPECT_DOUBLE_EQ(qx, 0.0);
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
