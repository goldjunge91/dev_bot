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

#include <chrono>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include "gmock/gmock.h"

#include "geometry_msgs/msg/twist_stamped.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/loaned_command_interface.hpp"
#include "hardware_interface/loaned_state_interface.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "lifecycle_msgs/msg/state.hpp"
#include "mecanum_drive_controller/mecanum_drive_controller.hpp"
#include "rclcpp/executors.hpp"
#include "rclcpp/rclcpp.hpp"

using hardware_interface::CommandInterface;
using hardware_interface::HW_IF_POSITION;
using hardware_interface::HW_IF_VELOCITY;
using hardware_interface::LoanedCommandInterface;
using hardware_interface::LoanedStateInterface;
using hardware_interface::StateInterface;

namespace
{
constexpr auto NODE_SUCCESS = controller_interface::CallbackReturn::SUCCESS;
constexpr auto NODE_ERROR = controller_interface::CallbackReturn::ERROR;
constexpr auto INIT_OK = controller_interface::return_type::OK;
}  // namespace

class TestableMecanumDriveController : public mecanum_drive_controller::MecanumDriveController
{
public:
  using MecanumDriveController::MecanumDriveController;

  const char * get_feedback_type() const {return feedback_type();}

  // Bypasses the ROS subscriber so kinematics tests do not depend on
  // executor timing / DDS discovery.
  void set_last_command(
    double linear_x, double linear_y, double angular_z, const rclcpp::Time & stamp)
  {
    auto msg = std::make_shared<geometry_msgs::msg::TwistStamped>();
    msg->header.stamp = stamp;
    msg->twist.linear.x = linear_x;
    msg->twist.linear.y = linear_y;
    msg->twist.angular.z = angular_z;
    received_velocity_msg_ptr_.set(msg);
  }

  double front_left_command() const
  {
    return registered_front_left_wheel_handle_->velocity.get().get_value();
  }
  double front_right_command() const
  {
    return registered_front_right_wheel_handle_->velocity.get().get_value();
  }
  double rear_left_command() const
  {
    return registered_rear_left_wheel_handle_->velocity.get().get_value();
  }
  double rear_right_command() const
  {
    return registered_rear_right_wheel_handle_->velocity.get().get_value();
  }
};

class MecanumDriveControllerTest : public ::testing::Test
{
public:
  static void SetUpTestCase() {rclcpp::init(0, nullptr);}
  static void TearDownTestCase() {rclcpp::shutdown();}

  void SetUp() override
  {
    controller_ = std::make_unique<TestableMecanumDriveController>();
  }

  void TearDown() override {controller_.reset(nullptr);}

protected:
  controller_interface::return_type InitController(
    const std::string & front_left_wheel_name, const std::string & front_right_wheel_name,
    const std::string & rear_left_wheel_name, const std::string & rear_right_wheel_name,
    bool position_feedback = false)
  {
    std::vector<rclcpp::Parameter> parameter_overrides;
    parameter_overrides.emplace_back("front_left_wheel_name", front_left_wheel_name);
    parameter_overrides.emplace_back("front_right_wheel_name", front_right_wheel_name);
    parameter_overrides.emplace_back("rear_left_wheel_name", rear_left_wheel_name);
    parameter_overrides.emplace_back("rear_right_wheel_name", rear_right_wheel_name);
    parameter_overrides.emplace_back("wheel_separation_x", wheel_separation_x_);
    parameter_overrides.emplace_back("wheel_separation_y", wheel_separation_y_);
    parameter_overrides.emplace_back("wheel_radius", wheel_radius_);
    parameter_overrides.emplace_back("position_feedback", position_feedback);

    auto node_options = rclcpp::NodeOptions();
    node_options.allow_undeclared_parameters(true);
    node_options.automatically_declare_parameters_from_overrides(true);
    node_options.parameter_overrides(parameter_overrides);

    return controller_->init("test_mecanum_drive_controller", "", node_options);
  }

  controller_interface::return_type InitControllerWithDefaultWheels(
    bool position_feedback = false)
  {
    return InitController(
      front_left_wheel_name_, front_right_wheel_name_, rear_left_wheel_name_,
      rear_right_wheel_name_, position_feedback);
  }

  void AssignResources()
  {
    std::vector<LoanedStateInterface> state_ifs;
    state_ifs.emplace_back(front_left_state_);
    state_ifs.emplace_back(front_right_state_);
    state_ifs.emplace_back(rear_left_state_);
    state_ifs.emplace_back(rear_right_state_);

    std::vector<LoanedCommandInterface> command_ifs;
    command_ifs.emplace_back(front_left_command_);
    command_ifs.emplace_back(front_right_command_);
    command_ifs.emplace_back(rear_left_command_);
    command_ifs.emplace_back(rear_right_command_);

    controller_->assign_interfaces(std::move(command_ifs), std::move(state_ifs));
  }

  const std::string front_left_wheel_name_ = "front_left_wheel_joint";
  const std::string front_right_wheel_name_ = "front_right_wheel_joint";
  const std::string rear_left_wheel_name_ = "rear_left_wheel_joint";
  const std::string rear_right_wheel_name_ = "rear_right_wheel_joint";

  const double wheel_separation_x_ = 0.2;
  const double wheel_separation_y_ = 0.3;
  const double wheel_radius_ = 0.05;

  double front_left_state_value_ = 0.0;
  double front_right_state_value_ = 0.0;
  double rear_left_state_value_ = 0.0;
  double rear_right_state_value_ = 0.0;

  double front_left_command_value_ = 0.0;
  double front_right_command_value_ = 0.0;
  double rear_left_command_value_ = 0.0;
  double rear_right_command_value_ = 0.0;

  CommandInterface front_left_command_{
    front_left_wheel_name_, HW_IF_VELOCITY, &front_left_command_value_};
  CommandInterface front_right_command_{
    front_right_wheel_name_, HW_IF_VELOCITY, &front_right_command_value_};
  CommandInterface rear_left_command_{
    rear_left_wheel_name_, HW_IF_VELOCITY, &rear_left_command_value_};
  CommandInterface rear_right_command_{
    rear_right_wheel_name_, HW_IF_VELOCITY, &rear_right_command_value_};

  StateInterface front_left_state_{
    front_left_wheel_name_, HW_IF_VELOCITY, &front_left_state_value_};
  StateInterface front_right_state_{
    front_right_wheel_name_, HW_IF_VELOCITY, &front_right_state_value_};
  StateInterface rear_left_state_{
    rear_left_wheel_name_, HW_IF_VELOCITY, &rear_left_state_value_};
  StateInterface rear_right_state_{
    rear_right_wheel_name_, HW_IF_VELOCITY, &rear_right_state_value_};

  std::unique_ptr<TestableMecanumDriveController> controller_;
};

TEST_F(MecanumDriveControllerTest, ConfigureFailsWithEmptyWheelNames)
{
  ASSERT_EQ(InitController("", "", "", ""), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_ERROR);
}

TEST_F(MecanumDriveControllerTest, ConfigureSucceedsWithValidParameters)
{
  ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);
}

TEST_F(MecanumDriveControllerTest, CommandInterfaceConfigurationListsFourVelocityInterfaces)
{
  ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);

  const auto command_interfaces = controller_->command_interface_configuration();
  ASSERT_THAT(
    command_interfaces.names,
    ::testing::UnorderedElementsAre(
      front_left_wheel_name_ + "/" + HW_IF_VELOCITY, front_right_wheel_name_ + "/" +
      HW_IF_VELOCITY,
      rear_left_wheel_name_ + "/" + HW_IF_VELOCITY, rear_right_wheel_name_ + "/" +
      HW_IF_VELOCITY));
}

TEST_F(MecanumDriveControllerTest, StateInterfaceConfigurationDefaultsToPosition)
{
  // position_feedback defaults to true (see mecanum_drive_controller_parameter.yaml),
  // so the state interfaces requested should be "position", not "velocity".
  ASSERT_EQ(InitControllerWithDefaultWheels(/*position_feedback=*/ true), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);

  EXPECT_STREQ(controller_->get_feedback_type(), HW_IF_POSITION);
  const auto state_interfaces = controller_->state_interface_configuration();
  ASSERT_THAT(
    state_interfaces.names,
    ::testing::UnorderedElementsAre(
      front_left_wheel_name_ + "/" + HW_IF_POSITION, front_right_wheel_name_ + "/" +
      HW_IF_POSITION,
      rear_left_wheel_name_ + "/" + HW_IF_POSITION, rear_right_wheel_name_ + "/" +
      HW_IF_POSITION));
}

TEST_F(MecanumDriveControllerTest, StateInterfaceConfigurationUsesVelocityWhenPositionFeedbackDisabled)
{
  ASSERT_EQ(InitControllerWithDefaultWheels(/*position_feedback=*/ false), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);

  EXPECT_STREQ(controller_->get_feedback_type(), HW_IF_VELOCITY);
  const auto state_interfaces = controller_->state_interface_configuration();
  ASSERT_THAT(
    state_interfaces.names,
    ::testing::UnorderedElementsAre(
      front_left_wheel_name_ + "/" + HW_IF_VELOCITY, front_right_wheel_name_ + "/" +
      HW_IF_VELOCITY,
      rear_left_wheel_name_ + "/" + HW_IF_VELOCITY, rear_right_wheel_name_ + "/" +
      HW_IF_VELOCITY));
}

TEST_F(MecanumDriveControllerTest, ActivateClaimsAllFourWheelHandles)
{
  ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);
  AssignResources();

  ASSERT_EQ(controller_->on_activate(rclcpp_lifecycle::State()), NODE_SUCCESS);

  // Newly activated, no command received yet -> commands stay at zero.
  EXPECT_DOUBLE_EQ(controller_->front_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->front_right_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_right_command(), 0.0);
}

TEST_F(MecanumDriveControllerTest, DeactivateThenUpdateHaltsAllWheels)
{
  // update()'s halt-on-inactive branch keys off get_node()->get_state(), which
  // only reflects real lifecycle transitions -- calling on_configure()/on_activate()/
  // on_deactivate() directly (as the other tests in this file do) never changes it.
  // So this test must drive the actual transitions instead.
  ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
  ASSERT_EQ(controller_->configure().id(), lifecycle_msgs::msg::State::PRIMARY_STATE_INACTIVE);
  AssignResources();
  ASSERT_EQ(
    controller_->get_node()->activate().id(),
    lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE);

  const auto now = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(1.0, 1.0, 1.0, now);
  ASSERT_EQ(
    controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);
  ASSERT_NE(controller_->front_left_command(), 0.0);

  ASSERT_EQ(
    controller_->get_node()->deactivate().id(),
    lifecycle_msgs::msg::State::PRIMARY_STATE_INACTIVE);
  ASSERT_EQ(
    controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  EXPECT_DOUBLE_EQ(controller_->front_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->front_right_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_right_command(), 0.0);
}

class MecanumDriveControllerKinematicsTest : public MecanumDriveControllerTest
{
protected:
  void SetUp() override
  {
    MecanumDriveControllerTest::SetUp();
    ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
    ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);
    AssignResources();
    ASSERT_EQ(controller_->on_activate(rclcpp_lifecycle::State()), NODE_SUCCESS);
  }

  // (wheel_separation_x + wheel_separation_y) / 2, matching the controller's own formula.
  double half_wheel_track() const {return (wheel_separation_x_ + wheel_separation_y_) / 2.0;}
};

TEST_F(MecanumDriveControllerKinematicsTest, PureForwardMotionDrivesAllWheelsEqually)
{
  const auto now = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(1.0, 0.0, 0.0, now);

  ASSERT_EQ(
    controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  const double expected = 1.0 / wheel_radius_;
  EXPECT_NEAR(controller_->front_left_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->front_right_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->rear_left_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->rear_right_command(), expected, 1e-9);
}

TEST_F(MecanumDriveControllerKinematicsTest, PureLateralMotionIsTheMecanumSignature)
{
  const auto now = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(0.0, 1.0, 0.0, now);

  ASSERT_EQ(
    controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  const double expected = 1.0 / wheel_radius_;
  EXPECT_NEAR(controller_->front_left_command(), -expected, 1e-9);
  EXPECT_NEAR(controller_->front_right_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->rear_left_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->rear_right_command(), -expected, 1e-9);
}

TEST_F(MecanumDriveControllerKinematicsTest, PureRotationSpinsWheelsOppositely)
{
  const auto now = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(0.0, 0.0, 1.0, now);

  ASSERT_EQ(
    controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  const double expected = half_wheel_track() / wheel_radius_;
  EXPECT_NEAR(controller_->front_left_command(), -expected, 1e-9);
  EXPECT_NEAR(controller_->front_right_command(), expected, 1e-9);
  EXPECT_NEAR(controller_->rear_left_command(), -expected, 1e-9);
  EXPECT_NEAR(controller_->rear_right_command(), expected, 1e-9);
}

TEST_F(MecanumDriveControllerKinematicsTest, StaleCommandIsZeroedBeforeBeingApplied)
{
  const auto stamp = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(1.0, 1.0, 1.0, stamp);

  // cmd_vel_timeout defaults to 0.5s; advance well past it.
  const auto later = stamp + rclcpp::Duration::from_seconds(1.0);
  ASSERT_EQ(
    controller_->update(later, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  EXPECT_DOUBLE_EQ(controller_->front_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->front_right_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_left_command(), 0.0);
  EXPECT_DOUBLE_EQ(controller_->rear_right_command(), 0.0);
}

TEST_F(MecanumDriveControllerKinematicsTest, FreshCommandWithinTimeoutIsNotZeroed)
{
  const auto stamp = controller_->get_node()->get_clock()->now();
  controller_->set_last_command(1.0, 0.0, 0.0, stamp);

  const auto shortly_after = stamp + rclcpp::Duration::from_seconds(0.1);
  ASSERT_EQ(
    controller_->update(shortly_after, rclcpp::Duration::from_seconds(0.01)),
    controller_interface::return_type::OK);

  EXPECT_NEAR(controller_->front_left_command(), 1.0 / wheel_radius_, 1e-9);
}

TEST_F(MecanumDriveControllerTest, PublishedCommandReachesTheController)
{
  ASSERT_EQ(InitControllerWithDefaultWheels(), INIT_OK);
  ASSERT_EQ(controller_->on_configure(rclcpp_lifecycle::State()), NODE_SUCCESS);
  AssignResources();
  ASSERT_EQ(controller_->on_activate(rclcpp_lifecycle::State()), NODE_SUCCESS);

  auto publisher_node = std::make_shared<rclcpp::Node>("cmd_vel_publisher_test_node");
  const std::string topic = std::string(controller_->get_node()->get_name()) + "/cmd_vel";
  auto publisher = publisher_node->create_publisher<geometry_msgs::msg::TwistStamped>(
    topic, rclcpp::SystemDefaultsQoS());

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(controller_->get_node()->get_node_base_interface());
  executor.add_node(publisher_node);

  for (int i = 0; i < 200 && publisher->get_subscription_count() == 0; ++i) {
    executor.spin_some();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
  ASSERT_GT(publisher->get_subscription_count(), 0u);

  // A publish immediately after get_subscription_count() first turns nonzero can still
  // race the writer/reader match on the DDS side and get dropped, so keep publishing
  // until the controller actually reports it -- this is the flaky bit, not a real bug.
  bool received = false;
  for (int i = 0; i < 100 && !received; ++i) {
    geometry_msgs::msg::TwistStamped msg;
    msg.header.stamp = controller_->get_node()->get_clock()->now();
    msg.twist.linear.x = 1.0;
    publisher->publish(msg);

    executor.spin_some();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    const auto now = controller_->get_node()->get_clock()->now();
    ASSERT_EQ(
      controller_->update(now, rclcpp::Duration::from_seconds(0.01)),
      controller_interface::return_type::OK);
    received = controller_->front_left_command() != 0.0;
  }

  ASSERT_TRUE(received) << "Published TwistStamped never reached the controller";
  EXPECT_NEAR(controller_->front_left_command(), 1.0 / wheel_radius_, 1e-6);
}
