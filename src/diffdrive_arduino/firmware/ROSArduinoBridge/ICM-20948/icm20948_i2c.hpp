#pragma once

#include "hardware/i2c.h"
#include "shared/Vector3f.hpp"

#include <cstddef>
#include <cstdint>

namespace hal::hardware {

class Icm20948 {
public:
    struct Config {
        i2c_inst_t* bus;
        uint32_t baudrate_hz;
        uint8_t address;
        uint8_t sda_pin;
        uint8_t scl_pin;
        bool enable_pullups;
    };

    explicit Icm20948(const Config& config);

    // Helper to create a Config for the right sensor (SDA=GP16, SCL=GP17)
    static Config rightSensorConfig(i2c_inst_t* bus,
                                    uint32_t baudrate_hz,
                                    uint8_t address,
                                    bool enable_pullups = true) {
        Config c{};
        c.bus = bus;
        c.baudrate_hz = baudrate_hz;
        c.address = address;
        c.sda_pin = 16;  // GP16
        c.scl_pin = 17;  // GP17
        c.enable_pullups = enable_pullups;
        return c;
    }

    bool initialize();
    bool readAcceleration(shared::Vector3f& accel_g);
    bool readGyroscope(shared::Vector3f& gyro_dps);
    bool readTemperature(float& temperature_c);

private:
    enum RegisterBank : uint8_t {
        Bank0 = 0,
        Bank1 = 1,
        Bank2 = 2,
        Bank3 = 3,
    };

    struct RawSample {
        int16_t x;
        int16_t y;
        int16_t z;
    };

    bool verifyWhoAmI();
    bool configurePower();
    bool configureSensors();
    bool selectRegisterBank(RegisterBank bank);
    bool writeRegister(RegisterBank bank, uint8_t reg, uint8_t value);
    bool readRegister(RegisterBank bank, uint8_t reg, uint8_t& value);
    bool readRegisters(RegisterBank bank, uint8_t reg, uint8_t* buffer, size_t length);
    bool readRawSample(RegisterBank bank, uint8_t start_reg, RawSample& sample);

    static float accelToG(int16_t raw_value);
    static float gyroToDps(int16_t raw_value);

    Config config_;
    RegisterBank current_bank_;
};

}  // namespace hal::hardware
