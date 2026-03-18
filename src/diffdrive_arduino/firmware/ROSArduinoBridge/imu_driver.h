/***************************************************************
   IMU driver – ICM-20948 via SPI0 (Pico RP2040)
   Adapter für ROSArduinoBridge Serial-Protokoll.
   Befehl 'i' liefert: "ax ay az gx gy gz\r\n"

   SPI0-Pins (Standard):
     SCLK = GP18 (SCLK am Chip)
     SDI  = GP19 (MOSI am Chip)
     ADA  = GP16 (MISO am Chip)
     NCS  = GP17 (CS am Chip)
 ***************************************************************/

#ifndef IMU_DRIVER_H
#define IMU_DRIVER_H

#if defined(ARDUINO_ARCH_RP2040)

// Schlanke Datenstruktur für IMU-Rohdaten
struct ImuData
{
  float ax = 0.0f;    // Beschleunigung X [g]
  float ay = 0.0f;    // Beschleunigung Y [g]
  float az = 0.0f;    // Beschleunigung Z [g]
  float gx = 0.0f;    // Winkelgeschwindigkeit X [dps]
  float gy = 0.0f;    // Winkelgeschwindigkeit Y [dps]
  float gz = 0.0f;    // Winkelgeschwindigkeit Z [dps]
};

// Initialisiert den ICM-20948 über SPI1
void imuSetup();

// Liest aktuelle Accel+Gyro-Werte. Gibt false zurück bei Fehler.
bool imuRead(ImuData & data);

// Trigger manual calibration and save to flash
void imuCalibrate();

// Load calibration from flash
void imuLoadCalibration();

#endif  // ARDUINO_ARCH_RP2040

#endif  // IMU_DRIVER_H
