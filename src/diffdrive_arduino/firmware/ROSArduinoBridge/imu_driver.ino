/***************************************************************
   IMU driver – ICM-20948 via SPI1 (Pico RP2040)
   Implementierung des imu_driver.h Adapters
 ***************************************************************/

#if defined(ARDUINO_ARCH_RP2040)

#include "hardware/flash.h"
#include "hardware/sync.h"
#include "icm20948_spi.hpp"
#include "imu_driver.h"

// Flash-Konfiguration für RP2040
// Wir nutzen einen Offset von 1.5MB (bei 2MB Flash), um sicher außer Reichweite des Programms zu
// sein.
#define IMU_CAL_FLASH_OFFSET (1536 * 1024)
#define IMU_CAL_MAGIC 0x494D5543  // "IMUC"

struct CalibrationFlashData {
    uint32_t magic;
    float gx_bias;
    float gy_bias;
    float gz_bias;
    uint32_t checksum;
};

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

void imuCalibrate() {
    if (!imuInitialized) return;

    if (imuSensor.calibrateGyro()) {
        // Kalibrierung erfolgreich, jetzt in Flash speichern
        Vec3 bias = imuSensor.getGyroBias();
        CalibrationFlashData flashData;
        flashData.magic = IMU_CAL_MAGIC;
        flashData.gx_bias = bias.x;
        flashData.gy_bias = bias.y;
        flashData.gz_bias = bias.z;
        flashData.checksum =
            (uint32_t)(bias.x * 1000) ^ (uint32_t)(bias.y * 1000) ^ (uint32_t)(bias.z * 1000);

        Serial.println("[IMU] Speichere Kalibrierung in Flash...");
        uint32_t ints = save_and_disable_interrupts();
        flash_range_erase(IMU_CAL_FLASH_OFFSET, FLASH_SECTOR_SIZE);
        flash_range_program(IMU_CAL_FLASH_OFFSET, (uint8_t *)&flashData, FLASH_PAGE_SIZE);
        restore_interrupts(ints);
        Serial.println("[IMU] Gespeichert.");
    }
}

void imuLoadCalibration() {
    if (!imuInitialized) return;

    Serial.println("[IMU] Suche Kalibrierung im Flash...");
    const CalibrationFlashData *flashData =
        (const CalibrationFlashData *)(XIP_BASE + IMU_CAL_FLASH_OFFSET);

    if (flashData->magic == IMU_CAL_MAGIC) {
        uint32_t expected_checksum = (uint32_t)(flashData->gx_bias * 1000) ^
                                     (uint32_t)(flashData->gy_bias * 1000) ^
                                     (uint32_t)(flashData->gz_bias * 1000);
        if (flashData->checksum == expected_checksum) {
            Vec3 bias = {flashData->gx_bias, flashData->gy_bias, flashData->gz_bias};
            imuSensor.setGyroBias(bias);
            Serial.print("[IMU] Kalibrierung geladen: ");
            Serial.print(bias.x, 4);
            Serial.print(", ");
            Serial.print(bias.y, 4);
            Serial.print(", ");
            Serial.println(bias.z, 4);
        } else {
            Serial.println("[IMU] Kalibrierung gefunden, aber Checksumme inkorrekt.");
        }
    } else {
        Serial.println("[IMU] Keine Kalibrierungsdaten gefunden.");
    }
}

#endif  // ARDUINO_ARCH_RP2040
