// Copyright 2024 Husarion
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <cmath>

#include "gmock/gmock.h"
#include "mecanum_drive_controller/speed_limiter.hpp"

using mecanum_drive_controller::SpeedLimiter;

TEST(SpeedLimiterTest, NoLimitsLeaveVelocityUnchanged)
{
  SpeedLimiter limiter;
  double v = 3.5;
  const double factor = limiter.limit(v, 0.0, 0.0, 0.1);
  EXPECT_DOUBLE_EQ(v, 3.5);
  EXPECT_DOUBLE_EQ(factor, 1.0);
}

TEST(SpeedLimiterTest, VelocityLimitClampsToMax)
{
  SpeedLimiter limiter(
    true, false, false,
    /*min_velocity=*/ NAN, /*max_velocity=*/ 1.0);
  double v = 5.0;
  limiter.limit_velocity(v);
  EXPECT_DOUBLE_EQ(v, 1.0);
}

TEST(SpeedLimiterTest, VelocityLimitDefaultsMinToNegativeMaxWhenUnspecified)
{
  SpeedLimiter limiter(
    true, false, false,
    /*min_velocity=*/ NAN, /*max_velocity=*/ 2.0);
  double v = -5.0;
  limiter.limit_velocity(v);
  EXPECT_DOUBLE_EQ(v, -2.0);
}

TEST(SpeedLimiterTest, VelocityLimitWithoutMaxThrows)
{
  EXPECT_THROW(
    SpeedLimiter(true, false, false, NAN, NAN),
    std::runtime_error);
}

TEST(SpeedLimiterTest, AccelerationLimitClampsDeltaV)
{
  // max_acceleration = 1.0 m/s^2, dt = 0.1s -> max dv = 0.1
  SpeedLimiter limiter(
    false, true, false,
    NAN, NAN, /*min_acceleration=*/ NAN, /*max_acceleration=*/ 1.0);
  double v = 5.0;
  const double v0 = 0.0;
  limiter.limit_acceleration(v, v0, 0.1);
  EXPECT_DOUBLE_EQ(v, 0.1);
}

TEST(SpeedLimiterTest, AccelerationLimitDefaultsMinToNegativeMax)
{
  SpeedLimiter limiter(
    false, true, false,
    NAN, NAN, /*min_acceleration=*/ NAN, /*max_acceleration=*/ 2.0);
  double v = -5.0;
  const double v0 = 0.0;
  limiter.limit_acceleration(v, v0, 0.1);
  EXPECT_DOUBLE_EQ(v, -0.2);
}

TEST(SpeedLimiterTest, AccelerationLimitWithoutMaxThrows)
{
  EXPECT_THROW(
    SpeedLimiter(false, true, false, NAN, NAN, NAN, NAN),
    std::runtime_error);
}

TEST(SpeedLimiterTest, JerkLimitClampsChangeInAcceleration)
{
  // max_jerk = 1.0 m/s^3, dt = 0.1s -> da_max = 2 * dt^2 * max_jerk = 0.02
  SpeedLimiter limiter(
    false, false, true,
    NAN, NAN, NAN, NAN, /*min_jerk=*/ NAN, /*max_jerk=*/ 1.0);
  double v = 100.0;
  const double v0 = 0.0;
  const double v1 = 0.0;
  limiter.limit_jerk(v, v0, v1, 0.1);
  EXPECT_DOUBLE_EQ(v, 0.02);
}

TEST(SpeedLimiterTest, JerkLimitWithoutMaxThrows)
{
  EXPECT_THROW(
    SpeedLimiter(false, false, true, NAN, NAN, NAN, NAN, NAN, NAN),
    std::runtime_error);
}

TEST(SpeedLimiterTest, LimitAppliesVelocityThenAccelerationThenJerkInOrder)
{
  // Only velocity limit active: acceleration/jerk clamps should not fire.
  SpeedLimiter limiter(
    true, false, false,
    NAN, /*max_velocity=*/ 0.5);
  double v = 10.0;
  const double factor = limiter.limit(v, 0.0, 0.0, 1.0);
  EXPECT_DOUBLE_EQ(v, 0.5);
  EXPECT_DOUBLE_EQ(factor, 0.05);
}

TEST(SpeedLimiterTest, LimitReturnsOneWhenRequestedVelocityIsZero)
{
  SpeedLimiter limiter(true, false, false, NAN, 1.0);
  double v = 0.0;
  const double factor = limiter.limit(v, 0.0, 0.0, 0.1);
  EXPECT_DOUBLE_EQ(factor, 1.0);
}
