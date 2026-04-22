// MIGRATION STATUS: COMPLETE (v2 — Arduino.h removed, pure Pico SDK)
// icm20948_spi.cpp — ICM-20948 SPI driver implementation.
// Ported from ROSArduinoBridge/icm20948_spi.cpp.
// All Serial.print() replaced with printf(); delay() → sleep_ms().
//
// Include order: hardware/spi.h first, so spi_inst_t is defined before
// icm20948_spi.hpp is parsed (header uses a forward declaration as fallback).

#include "hardware/spi.h"   // must be first — defines spi_inst_t / spi0 / spi1
#include "hardware/gpio.h"
#include "pico/stdlib.h"
#include "icm20948_spi.hpp"
#include <cstdio>
#include <cstdint>

namespace
{
// Register map (Bank 0 unless noted)
constexpr uint8_t REG_BANK_SEL = 0x7F;
constexpr uint8_t REG_WHO_AM_I = 0x00;
constexpr uint8_t REG_PWR_MGMT_1 = 0x06;
constexpr uint8_t REG_PWR_MGMT_2 = 0x07;
constexpr uint8_t REG_ACCEL_XOUT_H = 0x2D;
constexpr uint8_t REG_GYRO_XOUT_H = 0x33;
constexpr uint8_t REG_TEMP_OUT_H = 0x39;
// Bank 2
constexpr uint8_t REG_GYRO_CONFIG_1 = 0x01;
constexpr uint8_t REG_ACCEL_CONFIG = 0x14;

constexpr uint8_t WHO_AM_I_RESPONSE = 0xEA;
constexpr float ACC_SENS_2G = 16384.0f;
constexpr float GYRO_SENS_250DPS = 131.0f;
}  // namespace

namespace hal::hardware
{

Icm20948Simple::Icm20948Simple(const Config & config)
: config_(config), initialized_(false), current_bank_(0xFF) {}

bool Icm20948Simple::initialize()
{
  if (config_.bus == nullptr) {
    printf("[ICM20948] Invalid SPI bus\n");
    return false;
  }

  // Init SPI bus
  spi_init(config_.bus, config_.baudrate_hz);
  gpio_set_function(config_.sck_pin, GPIO_FUNC_SPI);
  gpio_set_function(config_.mosi_pin, GPIO_FUNC_SPI);
  gpio_set_function(config_.miso_pin, GPIO_FUNC_SPI);

  // CS pin
  gpio_init(config_.cs_pin);
  gpio_set_dir(config_.cs_pin, GPIO_OUT);
  gpio_put(config_.cs_pin, 1);
  sleep_ms(100);

  printf(
    "[ICM20948] SPI: CS=GP%d SCK=GP%d MOSI=GP%d MISO=GP%d @ %lu Hz\n",
    config_.cs_pin, config_.sck_pin,
    config_.mosi_pin, config_.miso_pin,
    (unsigned long)config_.baudrate_hz);

  // WHO_AM_I check — retry up to 3 times
  uint8_t whoami = 0;
  bool success = false;
  for (int attempt = 1; attempt <= 3 && !success; attempt++) {
    readRegisters(REG_WHO_AM_I, &whoami, 1);
    printf(
      "[ICM20948] WHO_AM_I attempt %d: 0x%02X (expected 0x%02X)\n",
      attempt, whoami, WHO_AM_I_RESPONSE);
    if (whoami == WHO_AM_I_RESPONSE) {success = true;} else {sleep_ms(50);}
  }
  if (!success) {
    printf("[ICM20948] WHO_AM_I FAILED — check wiring (CS/MISO)\n");
    return false;
  }

  // Wake sensor + enable all axes
  if (!writeRegister(REG_PWR_MGMT_1, 0x01)) {return false;}
  sleep_ms(50);
  if (!writeRegister(REG_PWR_MGMT_2, 0x00)) {return false;}

  // Configure: ±250 dps gyro, ±2 g accel
  if (!selectRegisterBank(2)) {return false;}
  if (!writeRegister(REG_GYRO_CONFIG_1, 0x01)) {return false;}
  if (!writeRegister(REG_ACCEL_CONFIG, 0x01)) {return false;}
  if (!selectRegisterBank(0)) {return false;}

  initialized_ = true;
  printf("[ICM20948] Initialised OK (CS=GP%d)\n", config_.cs_pin);
  return true;
}

bool Icm20948Simple::readRegisters(uint8_t reg, uint8_t * buffer, size_t length)
{
  uint8_t reg_addr = reg | 0x80;    // Set read bit
  gpio_put(config_.cs_pin, 0);
  spi_write_blocking(config_.bus, &reg_addr, 1);
  int n = spi_read_blocking(config_.bus, 0x00, buffer, length);
  gpio_put(config_.cs_pin, 1);
  return static_cast<size_t>(n) == length;
}

bool Icm20948Simple::writeRegister(uint8_t reg, uint8_t value)
{
  uint8_t data[2] = {static_cast<uint8_t>(reg & 0x7F), value};
  gpio_put(config_.cs_pin, 0);
  int n = spi_write_blocking(config_.bus, data, 2);
  gpio_put(config_.cs_pin, 1);
  return n == 2;
}

bool Icm20948Simple::selectRegisterBank(uint8_t bank)
{
  if (bank == current_bank_) {return true;}
  if (writeRegister(REG_BANK_SEL, static_cast<uint8_t>(bank << 4))) {
    current_bank_ = bank;
    return true;
  }
  return false;
}

bool Icm20948Simple::readAcceleration(Vec3 & accel_g)
{
  if (!initialized_) {return false;}
  uint8_t buf[6];
  if (!readRegisters(REG_ACCEL_XOUT_H, buf, 6)) {return false;}
  accel_g.x = static_cast<float>((int16_t)((buf[0] << 8) | buf[1])) / ACC_SENS_2G;
  accel_g.y = static_cast<float>((int16_t)((buf[2] << 8) | buf[3])) / ACC_SENS_2G;
  accel_g.z = static_cast<float>((int16_t)((buf[4] << 8) | buf[5])) / ACC_SENS_2G;
  return true;
}

bool Icm20948Simple::readGyroscope(Vec3 & gyro_dps)
{
  if (!initialized_) {return false;}
  uint8_t buf[6];
  if (!readRegisters(REG_GYRO_XOUT_H, buf, 6)) {return false;}
  gyro_dps.x = static_cast<float>((int16_t)((buf[0] << 8) | buf[1])) / GYRO_SENS_250DPS;
  gyro_dps.y = static_cast<float>((int16_t)((buf[2] << 8) | buf[3])) / GYRO_SENS_250DPS;
  gyro_dps.z = static_cast<float>((int16_t)((buf[4] << 8) | buf[5])) / GYRO_SENS_250DPS;
  return true;
}

bool Icm20948Simple::readTemperature(float & temperature_c)
{
  if (!initialized_) {return false;}
  uint8_t buf[2];
  if (!readRegisters(REG_TEMP_OUT_H, buf, 2)) {return false;}
  int16_t raw = (int16_t)((buf[0] << 8) | buf[1]);
  temperature_c = (static_cast<float>(raw) / 333.87f) + 21.0f;
  return true;
}

}  // namespace hal::hardware
