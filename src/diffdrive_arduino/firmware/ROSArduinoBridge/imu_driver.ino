/***************************************************************
   IMU driver – ICM-20948 via SPI1 (Pico RP2040)
   Implementierung des imu_driver.h Adapters
 ***************************************************************/

#if defined(ARDUINO_ARCH_RP2040)

#include "icm20948_spi.hpp"
#include "imu_driver.h"

// SPI0-Konfiguration
// SCLK=GP18, SDI=GP19 (MOSI), ADA=GP16 (MISO), NCS=GP17 (CS)
static hal::hardware::Icm20948Simple::Config imuConfig = {
    .bus = spi0,
    .baudrate_hz = 4000000,  // 4 MHz – sicher für ICM-20948
    .cs_pin = 17,
    .sck_pin = 18,
    .mosi_pin = 19,
    .miso_pin = 16};

static hal::hardware::Icm20948Simple imuSensor(imuConfig);
static bool imuInitialized = false;

void imuSetup() {
    imuInitialized = imuSensor.initialize();
    if (imuInitialized) {
        Serial.println("[IMU] ICM-20948 initialisiert (SPI0)");
    } else {
        Serial.println("[IMU] FEHLER: ICM-20948 initialisierung fehlgeschlagen!");
    }
}

bool imuRead(ImuData &data) {
    if (!imuInitialized) {
        return false;
    }

    Vec3 accel{}, gyro{};
    bool accelOk = imuSensor.readAcceleration(accel);
    bool gyroOk = imuSensor.readGyroscope(gyro);

    if (accelOk && gyroOk) {
        data.ax = accel.x;
        data.ay = accel.y;
        data.az = accel.z;
        data.gx = gyro.x;
        data.gy = gyro.y;
        data.gz = gyro.z;
        return true;
    }

    return false;
}

#endif  // ARDUINO_ARCH_RP2040
