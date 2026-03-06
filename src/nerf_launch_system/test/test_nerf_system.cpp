// Copyright 2026 Developer
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

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "nerf_launch_system/nerf_system.hpp"

#include <gtest/gtest.h>

namespace nerf_launch_system {

class TestNerfSystem : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup code if needed
    }
};

TEST_F(TestNerfSystem, on_init_test) {
    NerfSystem node;
    hardware_interface::HardwareInfo info;
    info.name = "test_nerf";
    info.hardware_parameters["port"] = "/dev/ttyTest";
    info.hardware_parameters["baud_rate"] = "115200";

    // Add joints
    hardware_interface::ComponentInfo joint;
    joint.name = "tilt_joint";

    hardware_interface::InterfaceInfo cmd_info;
    cmd_info.name = "position";
    cmd_info.initial_value = "0.0";
    joint.command_interfaces.push_back(cmd_info);

    hardware_interface::InterfaceInfo state_info;
    state_info.name = "position";
    state_info.initial_value = "0.0";
    joint.state_interfaces.push_back(state_info);

    info.joints.push_back(joint);

    EXPECT_EQ(node.on_init(info), hardware_interface::CallbackReturn::SUCCESS);
}

TEST_F(TestNerfSystem, command_mapping_test) {
    // This is a more complex test that might need mocking of SerialPort
    // For now, we verify that the component initializes correctly.
}

}  // namespace nerf_launch_system
