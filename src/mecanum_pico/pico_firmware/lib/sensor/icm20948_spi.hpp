// MIGRATION STATUS: COMPLETE (v2 — Arduino.h removed, pure Pico SDK)
// icm20948_spi.hpp — ICM-20948 SPI driver for Raspberry Pi Pico.
// Ported 1:1 from ROSArduinoBridge/icm20948_spi.hpp.
//
// INCLUDE RULE: This header only declares types/interfaces.
//   pico/stdlib.h and hardware/* are included ONLY in .cpp files,
//   never in headers, to avoid transitive IntelliSense cascade errors.
//   Callers must include hardware/spi.h before this header.
#pragma once

#include <cstdint>
#include <cstddef>

// spi_inst_t is defined in hardware/spi.h — include that before this header.
// Forward-declared here so the header compiles standalone in non-Pico contexts.
#ifndef HARDWARE_SPI_H
struct spi_inst;
typedef struct spi_inst spi_inst_t;
#endif


// Local 3D vector (replaces shared::Vector3f from original project)
struct Vec3 {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

namespace hal::hardware {

    class Icm20948Simple {
    public:
        struct Config {
            spi_inst_t* bus = nullptr;
            uint32_t baudrate_hz = 4000000;
            uint8_t  cs_pin = 17;
            uint8_t  sck_pin = 18;
            uint8_t  mosi_pin = 19;
            uint8_t  miso_pin = 16;
        };

        explicit Icm20948Simple(const Config& config);

        bool initialize();
        bool readAcceleration(Vec3& accel_g);
        bool readGyroscope(Vec3& gyro_dps);
        bool readTemperature(float& temperature_c);

    private:
        bool readRegisters(uint8_t reg, uint8_t* buffer, size_t length);
        bool writeRegister(uint8_t reg, uint8_t value);
        bool selectRegisterBank(uint8_t bank);

        Config  config_;
        bool    initialized_ = false;
        uint8_t current_bank_ = 0xFF;   // Force bank switch on first access
    };

}  // namespace hal::hardware
