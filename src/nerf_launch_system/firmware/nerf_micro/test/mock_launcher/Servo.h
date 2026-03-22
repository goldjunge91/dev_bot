// Servo.h Mock für native_launcher Tests
// GMock-basiert: EXPECT_CALL verifiziert attach/detach/writeMicroseconds
#pragma once
#include <gmock/gmock.h>
#include <cstdint>

class Servo {
public:
    MOCK_METHOD(void, attach, (int pin, int min, int max), ());
    MOCK_METHOD(void, detach, (), ());
    MOCK_METHOD(void, writeMicroseconds, (int us), ());
    MOCK_METHOD(bool, attached, (), (const));
};
