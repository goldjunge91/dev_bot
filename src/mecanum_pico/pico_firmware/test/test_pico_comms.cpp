// MIGRATION STATUS: COMPLETE (Sprint 2 — PicoComms serial protocol tests)
// Tests for PicoComms message formatting and encoder response parsing.
// No real serial hardware required — uses a MockPicoComms subclass.

#include <gtest/gtest.h>
#include "mecanum_pico/pico_comms.hpp"
#include <string>

// ---------------------------------------------------------------------------
// MockPicoComms — captures sent messages without opening a serial port
// ---------------------------------------------------------------------------
class MockPicoComms : public PicoComms
{
public:
  std::string last_sent;

  std::string send_msg(const std::string& msg_to_send, bool /*print_output*/ = false) override
  {
    last_sent = msg_to_send;
    return "";  // No real response in unit tests
  }
};

// ---------------------------------------------------------------------------
// PicoCommsFormatTest — verify outgoing message format
// ---------------------------------------------------------------------------

TEST(PicoCommsFormatTest, SetMotorValuesAllPositive)
{
  MockPicoComms comms;
  comms.set_motor_values(100, 200, 300, 400);
  EXPECT_EQ(comms.last_sent, "m 100 200 300 400\r");
}

TEST(PicoCommsFormatTest, SetMotorValuesAllNegative)
{
  MockPicoComms comms;
  comms.set_motor_values(-100, -200, -300, -400);
  EXPECT_EQ(comms.last_sent, "m -100 -200 -300 -400\r");
}

TEST(PicoCommsFormatTest, SetMotorValuesMixed)
{
  MockPicoComms comms;
  comms.set_motor_values(100, -100, 100, -100);
  EXPECT_EQ(comms.last_sent, "m 100 -100 100 -100\r");
}

TEST(PicoCommsFormatTest, SetMotorValuesAllZero)
{
  MockPicoComms comms;
  comms.set_motor_values(0, 0, 0, 0);
  EXPECT_EQ(comms.last_sent, "m 0 0 0 0\r");
}

TEST(PicoCommsFormatTest, EncoderRequestSendsCorrectFrame)
{
  MockPicoComms comms;
  int fl, fr, rl, rr;
  comms.read_encoder_values(fl, fr, rl, rr);
  EXPECT_EQ(comms.last_sent, "e\r");
}

// ---------------------------------------------------------------------------
// PicoCommsParseTest — verify incoming encoder response parsing
// ---------------------------------------------------------------------------

TEST(PicoCommsParseTest, ParseEncoderResponseValid)
{
  PicoComms comms;
  int fl = 0, fr = 0, rl = 0, rr = 0;
  bool ok = comms.parse_encoder_response("e 10 -10 10 -10\r\n", fl, fr, rl, rr);
  EXPECT_TRUE(ok);
  EXPECT_EQ(fl, 10);
  EXPECT_EQ(fr, -10);
  EXPECT_EQ(rl, 10);
  EXPECT_EQ(rr, -10);
}

TEST(PicoCommsParseTest, ParseEncoderResponseAllZero)
{
  PicoComms comms;
  int fl = 1, fr = 1, rl = 1, rr = 1;
  bool ok = comms.parse_encoder_response("e 0 0 0 0\r\n", fl, fr, rl, rr);
  EXPECT_TRUE(ok);
  EXPECT_EQ(fl, 0);
  EXPECT_EQ(fr, 0);
  EXPECT_EQ(rl, 0);
  EXPECT_EQ(rr, 0);
}

TEST(PicoCommsParseTest, ParseEncoderResponseLargeValues)
{
  PicoComms comms;
  int fl, fr, rl, rr;
  bool ok = comms.parse_encoder_response("e 1234 -1230 1231 -1228\r\n", fl, fr, rl, rr);
  EXPECT_TRUE(ok);
  EXPECT_EQ(fl, 1234);
  EXPECT_EQ(fr, -1230);
  EXPECT_EQ(rl, 1231);
  EXPECT_EQ(rr, -1228);
}

TEST(PicoCommsParseTest, ParseEncoderResponseMalformed_OnlyTwoValues)
{
  PicoComms comms;
  int fl = 0, fr = 0, rl = 0, rr = 0;
  bool ok = comms.parse_encoder_response("e 10 -10\r\n", fl, fr, rl, rr);
  EXPECT_FALSE(ok);
}

TEST(PicoCommsParseTest, ParseEncoderResponseMalformed_WrongPrefix)
{
  PicoComms comms;
  int fl, fr, rl, rr;
  bool ok = comms.parse_encoder_response("x 10 -10 10 -10\r\n", fl, fr, rl, rr);
  EXPECT_FALSE(ok);
}

TEST(PicoCommsParseTest, ParseEncoderResponseMalformed_EmptyString)
{
  PicoComms comms;
  int fl = 0, fr = 0, rl = 0, rr = 0;
  bool ok = comms.parse_encoder_response("", fl, fr, rl, rr);
  EXPECT_FALSE(ok);
}

// main is provided by test/test_main.cpp
