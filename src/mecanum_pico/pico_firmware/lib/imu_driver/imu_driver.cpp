// MIGRATION STATUS: COMPLETE (v2 — Arduino.h removed, pure Pico SDK)
// imu_driver.cpp — ICM-20948 adapter implementation.
// Ported from ROSArduinoBridge/imu_driver.ino.
// Serial.println() → printf(); C-linkage wrapper around C++ Icm20948Simple.
//
// hardware/spi.h is included HERE (not in headers) to resolve spi0/spi1.

// Include hardware/spi.h first so spi_inst_t and spi0 are defined
// before icm20948_spi.hpp and board_config.h are processed.
#include "hardware/spi.h"
#include "imu_driver.h"
#include "icm20948_spi.hpp"
#include "board_config.h"
#include <cstdio>

// Resolve numeric SPI index → Pico SDK pointer (IMU_SPI_IDX defined in board_config.h)
static spi_inst_t * const IMU_SPI_PORT = (IMU_SPI_IDX == 0) ? spi0 : spi1;

// Static C++ sensor object — hidden behind C API
static hal::hardware::Icm20948Simple::Config imu_config = {
  .bus = IMU_SPI_PORT,
  .baudrate_hz = IMU_BAUDRATE,
  .cs_pin = IMU_CS_PIN,
  .sck_pin = IMU_SCK_PIN,
  .mosi_pin = IMU_MOSI_PIN,
  .miso_pin = IMU_MISO_PIN,
};

static hal::hardware::Icm20948Simple imu_sensor(imu_config);
static bool imu_initialised = false;

// ---------------------------------------------------------------------------
// C-linkage API
// ---------------------------------------------------------------------------

void imu_setup(void)
{
  imu_initialised = imu_sensor.initialize();
  if (imu_initialised) {
    printf("[IMU] ICM-20948 ready (SPI CS=GP%d)\n", IMU_CS_PIN);
  } else {
    printf("[IMU] ICM-20948 FAILED — firmware continues in degraded mode\n");
  }
}

bool imu_read(ImuData * data)
{
  if (!imu_initialised || data == nullptr) {return false;}

  Vec3 accel{}, gyro{};
  bool ok = imu_sensor.readAcceleration(accel) && imu_sensor.readGyroscope(gyro);
  if (ok) {
    data->ax = accel.x; data->ay = accel.y; data->az = accel.z;
    data->gx = gyro.x;  data->gy = gyro.y;  data->gz = gyro.z;
  }
  return ok;
}
