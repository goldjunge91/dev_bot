// MIGRATION STATUS: SCAFFOLDING (Sprint 3 — hardware interface plugin load tests)
// These tests verify the MecanumPicoHardware plugin can be loaded via pluginlib
// and that it exports the correct number of interfaces.
// Full implementation will be wired in Sprint 3 after URDF is updated.

#include "hardware_interface/system_interface.hpp"
#include "pluginlib/class_loader.hpp"

#include <gtest/gtest.h>

// ---------------------------------------------------------------------------
// Sprint 3 — Plugin Load Test
// ---------------------------------------------------------------------------

TEST(HardwareInterfaceTest, PluginLoadsSuccessfully) {
    // TODO(sprint3): Uncomment once the package is built and installed.
    // pluginlib::ClassLoader<hardware_interface::SystemInterface> loader(
    //   "hardware_interface", "hardware_interface::SystemInterface");
    // auto hw = loader.createSharedInstance("mecanum_pico/MecanumPicoHardware");
    // ASSERT_NE(hw, nullptr);
    SUCCEED() << "Sprint 3 plugin load test: scaffolding in place, pending Sprint 3 build.";
}

TEST(HardwareInterfaceTest, ExportsFourCommandInterfaces) {
    // TODO(sprint3): Instantiate with mock HardwareInfo containing 4 joints.
    // Verify command_interfaces.size() == 4
    SUCCEED() << "Sprint 3: pending wiring.";
}

TEST(HardwareInterfaceTest, ExportsFourStateInterfaces) {
    // TODO(sprint3): Verify state_interfaces.size() == 8 (position + velocity per wheel)
    SUCCEED() << "Sprint 3: pending wiring.";
}

// main is provided by test/test_main.cpp
