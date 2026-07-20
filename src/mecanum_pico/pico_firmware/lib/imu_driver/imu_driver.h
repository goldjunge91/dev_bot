// MIGRATION STATUS: COMPLETE (v2 — Arduino.h removed, pure Pico SDK)
// imu_driver.h — ICM-20948 adapter for ROSArduinoBridge serial protocol.
// Command 'i' replies: "ax ay az gx gy gz\n"
//
// Default SPI0 pins (from ROSArduinoBridge README):
//   CS=GP17  SCK=GP18  MOSI=GP19  MISO=GP16
// Override in board_config.h if needed.

#ifndef IMU_DRIVER_H
#define IMU_DRIVER_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

    // IMU raw data (SI-adjacent units matching original imu_driver.h)
    typedef struct {
        float ax;  ///< Acceleration X [g]
        float ay;  ///< Acceleration Y [g]
        float az;  ///< Acceleration Z [g]
        float gx;  ///< Angular rate X [dps]
        float gy;  ///< Angular rate Y [dps]
        float gz;  ///< Angular rate Z [dps]
    } ImuData;

    /** Initialise ICM-20948 via SPI. Call once in main() after stdio init. */
    void imu_setup(void);

    /**
     * @brief Read latest accel + gyro values.
     * @return true on success; false if sensor not initialised or read failed.
     */
    bool imu_read(ImuData *data);

#ifdef __cplusplus
}
#endif

#endif  // IMU_DRIVER_H
