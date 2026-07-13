#include <gtest/gtest.h>
#include <pluginlib/class_loader.hpp>
#include <hardware_interface/system_interface.hpp>
#include <exception>

TEST(HardwareInterfaceTest, PluginLoadsSuccessfully) {
  pluginlib::ClassLoader<hardware_interface::SystemInterface> loader(
    "hardware_interface", "hardware_interface::SystemInterface");
  
  try {
    auto hw = loader.createSharedInstance("mecanum_pico/MecanumPicoHardware");
    ASSERT_NE(hw, nullptr);
  } catch (const std::exception & e) {
    FAIL() << "Failed to load hardware interface plugin: " << e.what();
  }
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}

