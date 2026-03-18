#pragma once

#include "hardware/spi.h"
// #include "shared/Vector3f.hpp"  // Entfernt: war Teil des alten FreeRTOS-Projekts

#include <cstddef>
#include <cstdint>

// Lokale 3D-Vektor-Struct als Ersatz fuer shared::Vector3f
struct Vec3
{
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
};

namespace hal::hardware
{

class Icm20948Simple
{
public:
  struct Config
  {
    spi_inst_t * bus;
    uint32_t baudrate_hz;
    uint8_t cs_pin;
    uint8_t sck_pin;
    uint8_t mosi_pin;
    uint8_t miso_pin;
  };

  explicit Icm20948Simple(const Config & config);

  bool initialize();
  bool calibrateGyro(int num_samples = 200);
  void setGyroBias(Vec3 bias)
  {
    gyro_bias_ = bias;
  }
  Vec3 getGyroBias() const
  {
    return gyro_bias_;
  }
  bool readAcceleration(Vec3 & accel_g);
  bool readGyroscope(Vec3 & gyro_dps);
  bool readTemperature(float & temperature_c);

private:
  bool readRegisters(uint8_t reg, uint8_t * buffer, size_t length);
  bool writeRegister(uint8_t reg, uint8_t value);
  bool selectRegisterBank(uint8_t bank);

  Config config_;
  bool initialized_ = false;
  uint8_t current_bank_ = 0xFF;    // Ungültiger Startwert, um Umschaltung zu erzwingen
  Vec3 gyro_bias_ = {0.0f, 0.0f, 0.0f};
};

}  // namespace hal::hardware
