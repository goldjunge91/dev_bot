#include <gtest/gtest.h>
#include "mecanum_pico/wheel.hpp"

// Test: Wheel stores name correctly
TEST(WheelTest, NameIsSetOnConstruction) {
  Wheel w("front_left_wheel_joint", 20);
  EXPECT_EQ(w.name, "front_left_wheel_joint");
}

// Test: encoder ticks to radians conversion
TEST(WheelTest, CalcEncAngleCorrect) {
  Wheel w("test", 20);  // 20 ticks/rev
  w.enc = 10;
  w.pos = w.calc_enc_angle();
  EXPECT_NEAR(w.pos, M_PI, 1e-9);  // 10/20 * 2pi = pi
}

// Test: 4-wheel struct holds all wheels independently
TEST(FourWheelTest, WheelsAreIndependent) {
  Wheel fl("fl", 20), fr("fr", 20), rl("rl", 20), rr("rr", 20);
  fl.cmd = 1.0; fr.cmd = 2.0; rl.cmd = 3.0; rr.cmd = 4.0;
  EXPECT_DOUBLE_EQ(fl.cmd, 1.0);
  EXPECT_DOUBLE_EQ(rr.cmd, 4.0);
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}

