#include <gtest/gtest.h>
#include "mecanum_pico/pico_comms.hpp"

// Mock: replace PicoComms with a testable subclass that records sent strings
class MockPicoComms : public PicoComms {
public:
  std::string last_sent;
  std::string send_msg(const std::string & msg, bool /*print_output*/ = false) override {
    last_sent = msg;
    // Return a dummy valid response when requesting encoders
    if (msg == "e\r") {
      return "e 123 -456 789 -1011\r\n";
    }
    return "OK\r\n";
  }
};

TEST(PicoCommsTest, SetMotorValuesFormatsCorrectly) {
  MockPicoComms comms;
  comms.set_motor_values(100, -100, 200, -200);
  EXPECT_EQ(comms.last_sent, "m 100 -100 200 -200\r");
}

TEST(PicoCommsTest, ParseEncoderResponseValid) {
  MockPicoComms comms;
  int fl, fr, rl, rr;
  bool ok = comms.parse_encoder_response("e 10 -10 20 -20\r\n", fl, fr, rl, rr);
  EXPECT_TRUE(ok);
  EXPECT_EQ(fl, 10);
  EXPECT_EQ(fr, -10);
  EXPECT_EQ(rl, 20);
  EXPECT_EQ(rr, -20);
}

TEST(PicoCommsTest, ParseEncoderResponseMalformed) {
  MockPicoComms comms;
  int fl, fr, rl, rr;
  bool ok = comms.parse_encoder_response("e 10 -10 20\r\n", fl, fr, rl, rr);  // only 3 values
  EXPECT_FALSE(ok);
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}

