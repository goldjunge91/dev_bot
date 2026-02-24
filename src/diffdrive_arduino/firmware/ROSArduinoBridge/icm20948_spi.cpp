#include "icm20948_spi.hpp"

#include "pico/stdlib.h"

#include <Arduino.h>
#include <cstdio>

namespace {
// Register
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

// Skalierungsfaktoren
constexpr float ACC_SENS_2G = 16384.0f;
constexpr float GYRO_SENS_250DPS = 131.0f;
}  // namespace

namespace hal::hardware {

Icm20948Simple::Icm20948Simple(const Config &config) : config_(config), initialized_(false) {}

bool Icm20948Simple::initialize() {
    if (config_.bus == nullptr) {
        Serial.println("[ICM20948-SPI] Invalid SPI bus");
        return false;
    }

    // SPI-Bus initialisieren
    spi_init(config_.bus, config_.baudrate_hz);
    gpio_set_function(config_.sck_pin, GPIO_FUNC_SPI);
    gpio_set_function(config_.mosi_pin, GPIO_FUNC_SPI);
    gpio_set_function(config_.miso_pin, GPIO_FUNC_SPI);

    // Chip Select Pin initialisieren
    gpio_init(config_.cs_pin);
    gpio_set_dir(config_.cs_pin, GPIO_OUT);
    gpio_put(config_.cs_pin, 1);  // Deselektieren

    delay(100);

    // SPI pin diagnostics
    Serial.print("[ICM20948-SPI] Pin config: CS=");
    Serial.print(config_.cs_pin);
    Serial.print(", SCK=");
    Serial.print(config_.sck_pin);
    Serial.print(", SDI=");
    Serial.print(config_.mosi_pin);
    Serial.print(", ADA=");
    Serial.println(config_.miso_pin);
    Serial.print("[ICM20948-SPI] SPI baudrate: ");
    Serial.print(config_.baudrate_hz);
    Serial.println(" Hz");

    // WHO_AM_I-Register prüfen (try multiple times)
    uint8_t whoami = 0;
    const int max_attempts = 3;
    bool success = false;

    for (int attempt = 1; attempt <= max_attempts && !success; attempt++) {
        readRegisters(REG_WHO_AM_I, &whoami, 1);
        Serial.print("[ICM20948-SPI] WHO_AM_I attempt ");
        Serial.print(attempt);
        Serial.print(": read 0x");
        Serial.print(whoami, HEX);
        Serial.print(" (expected 0x");
        Serial.print(WHO_AM_I_RESPONSE, HEX);
        Serial.println(")");

        if (whoami == WHO_AM_I_RESPONSE) {
            success = true;
        } else if (attempt < max_attempts) {
            delay(50);
        }
    }

    if (!success) {
        Serial.print("[ICM20948-SPI] ❌ WHO_AM_I verification FAILED after ");
        Serial.print(max_attempts);
        Serial.println(" attempts");
        Serial.println("[ICM20948-SPI] Mögliche Ursachen:");
        Serial.print("  - Kabelsalat am ADA (MISO) Pin? (GPIO ");
        Serial.print(config_.miso_pin);
        Serial.println(")");
        Serial.print("  - CS Pin falsch oder nicht verbunden? (GPIO ");
        Serial.print(config_.cs_pin);
        Serial.println(")");
        Serial.println("  - Sensor hat keinen Strom oder ist defekt");
        return false;
    }

    // Sensor aufwecken
    if (!writeRegister(REG_PWR_MGMT_1, 0x01)) return false;
    delay(50);
    // Alle Achsen aktivieren
    if (!writeRegister(REG_PWR_MGMT_2, 0x00)) return false;

    // Sensoren konfigurieren
    if (!selectRegisterBank(2)) return false;
    if (!writeRegister(REG_GYRO_CONFIG_1, 0x01)) return false;  // ±250dps
    if (!writeRegister(REG_ACCEL_CONFIG, 0x01)) return false;   // ±2g
    if (!selectRegisterBank(0)) return false;

    initialized_ = true;
    Serial.print("[ICM20948-SPI] Sensor initialised (CS=");
    Serial.print(config_.cs_pin);
    Serial.println(")");
    return true;
}

bool Icm20948Simple::readRegisters(uint8_t reg, uint8_t *buffer, size_t length) {
    uint8_t reg_addr = reg | 0x80;  // Lese-Bit setzen

    gpio_put(config_.cs_pin, 0);  // Selektieren
    spi_write_blocking(config_.bus, &reg_addr, 1);
    int read_count = spi_read_blocking(config_.bus, 0x00, buffer, length);
    gpio_put(config_.cs_pin, 1);  // Deselektieren

    return static_cast<size_t>(read_count) == length;
}

bool Icm20948Simple::writeRegister(uint8_t reg, uint8_t value) {
    uint8_t reg_addr = reg & 0x7F;  // Schreib-Bit löschen
    uint8_t data[2] = {reg_addr, value};

    gpio_put(config_.cs_pin, 0);  // Selektieren
    int write_count = spi_write_blocking(config_.bus, data, 2);
    gpio_put(config_.cs_pin, 1);  // Deselektieren

    return write_count == 2;
}

bool Icm20948Simple::selectRegisterBank(uint8_t bank) {
    if (bank == current_bank_) return true;
    if (writeRegister(REG_BANK_SEL, bank << 4)) {
        current_bank_ = bank;
        return true;
    }
    return false;
}

bool Icm20948Simple::readAcceleration(Vec3 &accel_g) {
    if (!initialized_) return false;

    uint8_t buffer[6];
    if (!readRegisters(REG_ACCEL_XOUT_H, buffer, 6)) return false;

    int16_t raw_x = (buffer[0] << 8) | buffer[1];
    int16_t raw_y = (buffer[2] << 8) | buffer[3];
    int16_t raw_z = (buffer[4] << 8) | buffer[5];

    accel_g.x = static_cast<float>(raw_x) / ACC_SENS_2G;
    accel_g.y = static_cast<float>(raw_y) / ACC_SENS_2G;
    accel_g.z = static_cast<float>(raw_z) / ACC_SENS_2G;
    return true;
}

bool Icm20948Simple::readGyroscope(Vec3 &gyro_dps) {
    if (!initialized_) return false;

    uint8_t buffer[6];
    if (!readRegisters(REG_GYRO_XOUT_H, buffer, 6)) return false;

    int16_t raw_x = (buffer[0] << 8) | buffer[1];
    int16_t raw_y = (buffer[2] << 8) | buffer[3];
    int16_t raw_z = (buffer[4] << 8) | buffer[5];

    gyro_dps.x = static_cast<float>(raw_x) / GYRO_SENS_250DPS;
    gyro_dps.y = static_cast<float>(raw_y) / GYRO_SENS_250DPS;
    gyro_dps.z = static_cast<float>(raw_z) / GYRO_SENS_250DPS;
    return true;
}

bool Icm20948Simple::readTemperature(float &temperature_c) {
    if (!initialized_) return false;

    uint8_t buffer[2];
    if (!readRegisters(REG_TEMP_OUT_H, buffer, 2)) return false;

    int16_t raw_temp = (buffer[0] << 8) | buffer[1];
    temperature_c = (static_cast<float>(raw_temp) / 333.87f) + 21.0f;
    return true;
}

}  // namespace hal::hardware
