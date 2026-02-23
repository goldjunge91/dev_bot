/***************************************************************
   IMU driver – ICM-20948 via SPI1 (Pico RP2040)
   Implementierung des imu_driver.h Adapters
 ***************************************************************/

#if defined(ARDUINO_ARCH_RP2040)

#include "ICM-20948/icm20948_spi.hpp"
#include "imu_driver.h"

// SPI1-Konfiguration
// SCK=GP14, MOSI=GP15, MISO=GP12, CS=GP13
static hal::hardware::Icm20948Simple::Config imuConfig = {
    .bus = spi1,
    .baudrate_hz = 4000000,  // 4 MHz – sicher für ICM-20948
    .cs_pin = 13,
    .sck_pin = 14,
    .mosi_pin = 15,
    .miso_pin = 12};

static hal::hardware::Icm20948Simple imuSensor(imuConfig);
static bool imuInitialized = false;

void imuSetup() {
    imuInitialized = imuSensor.initialize();
    if (imuInitialized) {
        Serial.println("[IMU] ICM-20948 initialisiert (SPI1)");
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
