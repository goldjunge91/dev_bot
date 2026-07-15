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
#include <memory>

#include "gmock/gmock.h"
#include "mecanum_drive_controller/odometry.hpp"
#include "rclcpp/time.hpp"

using mecanum_drive_controller::Odometry;

namespace
{
// Window size 1 makes the rolling-mean accumulator return the raw sample,
// which keeps the expected values in these tests easy to reason about.
constexpr size_t kSingleSampleWindow = 1;
}  // namespace

class OdometryTest : public ::testing::Test
{
protected:
  void SetUp() override
  {
    odometry_ = std::make_unique<Odometry>(kSingleSampleWindow);
    // wheel_separation_x=0.5, wheel_separation_y=0.3, wheel_radius=1.0
    // -> (sep_x + sep_y) / 2 = 0.4, matching the denominator used for angular velocity.
    odometry_->setWheelParams(0.5, 0.3, 1.0);
    odometry_->init(rclcpp::Time(0, 0, RCL_ROS_TIME));
  }

  std::unique_ptr<Odometry> odometry_;
};

TEST_F(OdometryTest, ForwardMotionFromAllWheelsEqual)
{
  const rclcpp::Time t(0, 100000000, RCL_ROS_TIME);  // +0.1s
  odometry_->updateFromVelocity(1.0, 1.0, 1.0, 1.0, t);

  EXPECT_NEAR(odometry_->getX(), 1.0, 1e-9);
  EXPECT_NEAR(odometry_->getY(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getHeading(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getLinearX(), 10.0, 1e-6);
  EXPECT_NEAR(odometry_->getLinearY(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getAngular(), 0.0, 1e-9);
}

TEST_F(OdometryTest, LateralMotionIsTheMecanumSignature)
{
  // fl=-1, fr=1, rl=1, rr=-1 -> pure sideways (+y) translation, no rotation.
  const rclcpp::Time t(0, 100000000, RCL_ROS_TIME);  // +0.1s
  odometry_->updateFromVelocity(-1.0, 1.0, 1.0, -1.0, t);

  EXPECT_NEAR(odometry_->getX(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getY(), 1.0, 1e-9);
  EXPECT_NEAR(odometry_->getHeading(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getLinearX(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getLinearY(), 10.0, 1e-6);
  EXPECT_NEAR(odometry_->getAngular(), 0.0, 1e-9);
}

TEST_F(OdometryTest, PureRotationInPlace)
{
  // fl=-1, fr=1, rl=-1, rr=1 -> pure rotation, no translation.
  // angular = (-fl+fr-rl+rr) / (4 * (sep_x+sep_y)/2) = 4 / 1.6 = 2.5 [rad per call]
  const rclcpp::Time t(0, 100000000, RCL_ROS_TIME);  // +0.1s
  odometry_->updateFromVelocity(-1.0, 1.0, -1.0, 1.0, t);

  EXPECT_NEAR(odometry_->getX(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getY(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getHeading(), 2.5, 1e-9);
  EXPECT_NEAR(odometry_->getAngular(), 25.0, 1e-6);
}

TEST_F(OdometryTest, UpdateFromVelocityWithoutElapsedTimeStillIntegrates)
{
  // dt == 0 is allowed for updateFromVelocity (unlike update(), it has no
  // early-return guard) but produces an infinite velocity estimate.
  const rclcpp::Time t(0, 0, RCL_ROS_TIME);
  const bool result = odometry_->updateFromVelocity(1.0, 1.0, 1.0, 1.0, t);
  EXPECT_TRUE(result);
  EXPECT_TRUE(std::isinf(odometry_->getLinearX()));
}

TEST_F(OdometryTest, PositionUpdateReturnsFalseForTooSmallInterval)
{
  const rclcpp::Time t(0, 0, RCL_ROS_TIME);
  EXPECT_FALSE(odometry_->update(1.0, 1.0, 1.0, 1.0, t));
}

TEST_F(OdometryTest, OpenLoopIntegratesCommandedVelocityDirectly)
{
  const rclcpp::Time t(0, 500000000, RCL_ROS_TIME);  // +0.5s
  odometry_->updateOpenLoop(2.0, 0.0, 0.0, t);

  EXPECT_NEAR(odometry_->getX(), 1.0, 1e-9);  // 2.0 m/s * 0.5s
  EXPECT_NEAR(odometry_->getY(), 0.0, 1e-9);
  EXPECT_NEAR(odometry_->getLinearX(), 2.0, 1e-9);  // stored directly, no averaging
}

TEST_F(OdometryTest, ResetOdometryClearsPoseButKeepsVelocity)
{
  const rclcpp::Time t(0, 100000000, RCL_ROS_TIME);
  odometry_->updateFromVelocity(1.0, 1.0, 1.0, 1.0, t);
  ASSERT_NE(odometry_->getX(), 0.0);

  odometry_->resetOdometry();

  EXPECT_DOUBLE_EQ(odometry_->getX(), 0.0);
  EXPECT_DOUBLE_EQ(odometry_->getY(), 0.0);
  EXPECT_DOUBLE_EQ(odometry_->getHeading(), 0.0);
  // Velocity estimates are not part of "pose" and survive the reset.
  EXPECT_NEAR(odometry_->getLinearX(), 10.0, 1e-6);
}
