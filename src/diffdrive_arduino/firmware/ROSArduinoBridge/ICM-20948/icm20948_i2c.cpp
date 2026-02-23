#include "icm20948_i2c.hpp"

#include <hardware/gpio.h>
#include <hardware/i2c.h>
#include <pico/stdlib.h>

namespace {
constexpr uint8_t REG_BANK_SEL = 0x7F;
constexpr uint8_t REG_WHO_AM_I = 0x00;
constexpr uint8_t REG_PWR_MGMT_1 = 0x06;
constexpr uint8_t REG_PWR_MGMT_2 = 0x07;
constexpr uint8_t REG_ACCEL_XOUT_H = 0x2D;
constexpr uint8_t REG_GYRO_XOUT_H = 0x33;
constexpr uint8_t REG_TEMP_OUT_H = 0x39;

// Bank 2 configuration registers
constexpr uint8_t REG_GYRO_CONFIG_1 = 0x01;
constexpr uint8_t REG_ACCEL_CONFIG = 0x14;
constexpr uint8_t REG_ACCEL_SMPLRT_DIV_1 = 0x10;
constexpr uint8_t REG_ACCEL_SMPLRT_DIV_2 = 0x11;
constexpr uint8_t REG_GYRO_SMPLRT_DIV = 0x00;

constexpr uint8_t WHO_AM_I_RESPONSE = 0xEA;

constexpr float ACC_SENS_2G = 16384.0f;
constexpr float GYRO_SENS_250DPS = 131.0f;

constexpr uint8_t BANK_SHIFT = 4;
}  // namespace

namespace hal::hardware {

Icm20948::Icm20948(const Config& config) : config_(config), current_bank_(Bank0) {}

// Example helper: create default right-side sensor instance
Icm20948
make_right_icm(i2c_inst_t* bus, uint32_t baud, uint8_t address) {
    Icm20948::Config cfg = Icm20948::rightSensorConfig(bus, baud, address, true);
    return Icm20948(cfg);
}

bool
Icm20948::initialize() {
    if(config_.bus == nullptr) {
        return false;
    }

    i2c_init(config_.bus, config_.baudrate_hz);
    gpio_set_function(config_.sda_pin, GPIO_FUNC_I2C);
    gpio_set_function(config_.scl_pin, GPIO_FUNC_I2C);
    if(config_.enable_pullups) {
        gpio_pull_up(config_.sda_pin);
        gpio_pull_up(config_.scl_pin);
    }

    sleep_ms(10);

    if(!verifyWhoAmI()) {
        return false;
    }

    if(!configurePower()) {
        return false;
    }

    return configureSensors();
}

bool
Icm20948::readAcceleration(shared::Vector3f& accel_g) {
    RawSample sample{};
    if(!readRawSample(Bank0, REG_ACCEL_XOUT_H, sample)) {
        return false;
    }

    accel_g.x = accelToG(sample.x);
    accel_g.y = accelToG(sample.y);
    accel_g.z = accelToG(sample.z);
    return true;
}

bool
Icm20948::readGyroscope(shared::Vector3f& gyro_dps) {
    RawSample sample{};
    if(!readRawSample(Bank0, REG_GYRO_XOUT_H, sample)) {
        return false;
    }

    gyro_dps.x = gyroToDps(sample.x);
    gyro_dps.y = gyroToDps(sample.y);
    gyro_dps.z = gyroToDps(sample.z);
    return true;
}

bool
Icm20948::readTemperature(float& temperature_c) {
    uint8_t buffer[2] = {0, 0};
    if(!readRegisters(Bank0, REG_TEMP_OUT_H, buffer, sizeof(buffer))) {
        return false;
    }

    int16_t raw_temp = static_cast<int16_t>((buffer[0] << 8) | buffer[1]);
    temperature_c = (static_cast<float>(raw_temp) / 333.87f) + 21.0f;
    return true;
}

bool
Icm20948::verifyWhoAmI() {
    uint8_t value = 0;
    if(!readRegister(Bank0, REG_WHO_AM_I, value)) {
        return false;
    }
    return value == WHO_AM_I_RESPONSE;
}

bool
Icm20948::configurePower() {
    // Wake the device and select auto clock mode (best available clock source)
    if(!writeRegister(Bank0, REG_PWR_MGMT_1, 0x01)) {
        return false;
    }

    // Ensure all sensors are enabled (clear standby bits)
    return writeRegister(Bank0, REG_PWR_MGMT_2, 0x00);
}

bool
Icm20948::configureSensors() {
    if(!selectRegisterBank(Bank2)) {
        return false;
    }

    // Set gyro to 250 dps full scale, enable DLPF at configuration 2 (~111 Hz bandwidth)
    if(!writeRegister(Bank2, REG_GYRO_CONFIG_1, 0x12)) {
        return false;
    }

    // Set accelerometer to ±2g full scale, enable DLPF at configuration 2 (~111 Hz bandwidth)
    if(!writeRegister(Bank2, REG_ACCEL_CONFIG, 0x12)) {
        return false;
    }

    // Use the highest output data rate for now (divider 0)
    if(!writeRegister(Bank2, REG_GYRO_SMPLRT_DIV, 0x00)) {
        return false;
    }
    if(!writeRegister(Bank2, REG_ACCEL_SMPLRT_DIV_1, 0x00)) {
        return false;
    }
    if(!writeRegister(Bank2, REG_ACCEL_SMPLRT_DIV_2, 0x00)) {
        return false;
    }

    // Return to bank 0 for data reads
    return selectRegisterBank(Bank0);
}

bool
Icm20948::selectRegisterBank(RegisterBank bank) {
    if(bank == current_bank_) {
        return true;
    }

    uint8_t payload[2] = {REG_BANK_SEL, static_cast<uint8_t>(bank) << BANK_SHIFT};
    int written = i2c_write_blocking(config_.bus, config_.address, payload, 2, false);
    if(written == 2) {
        current_bank_ = bank;
        return true;
    }

    return false;
}

bool
Icm20948::writeRegister(RegisterBank bank, uint8_t reg, uint8_t value) {
    if(!selectRegisterBank(bank)) {
        return false;
    }

    uint8_t buffer[2] = {reg, value};
    int written = i2c_write_blocking(config_.bus, config_.address, buffer, 2, false);
    return written == 2;
}

bool
Icm20948::readRegister(RegisterBank bank, uint8_t reg, uint8_t& value) {
    return readRegisters(bank, reg, &value, 1);
}

bool
Icm20948::readRegisters(RegisterBank bank, uint8_t reg, uint8_t* buffer, size_t length) {
    if(!selectRegisterBank(bank)) {
        return false;
    }

    uint8_t reg_addr = reg;
    int rc = i2c_write_blocking(config_.bus, config_.address, &reg_addr, 1, true);
    if(rc != 1) {
        return false;
    }

    rc = i2c_read_blocking(config_.bus, config_.address, buffer, length, false);
    return (rc == static_cast<int>(length));
}

bool
Icm20948::readRawSample(RegisterBank bank, uint8_t start_reg, RawSample& sample) {
    uint8_t buffer[6] = {0};
    if(!readRegisters(bank, start_reg, buffer, sizeof(buffer))) {
        return false;
    }

    sample.x = static_cast<int16_t>((buffer[0] << 8) | buffer[1]);
    sample.y = static_cast<int16_t>((buffer[2] << 8) | buffer[3]);
    sample.z = static_cast<int16_t>((buffer[4] << 8) | buffer[5]);
    return true;
}

float
Icm20948::accelToG(int16_t raw_value) {
    return static_cast<float>(raw_value) / ACC_SENS_2G;
}

float
Icm20948::gyroToDps(int16_t raw_value) {
    return static_cast<float>(raw_value) / GYRO_SENS_250DPS;
}

}  // namespace hal::hardware
