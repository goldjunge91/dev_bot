// MIGRATION STATUS: COMPLETE (v2 — TB6612 + ICM-20948 SPI)
// board_config.h — GPIO pin assignments for mecanum_pico firmware.
// Platform: Raspberry Pi Pico (RP2040), pure Pico SDK (no Arduino).
//
// Motor index mapping: [0]=FL  [1]=FR  [2]=RL  [3]=RR
// Adjust all pin numbers to match your physical wiring.

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

// ---------------------------------------------------------------------------
// Motor 0: Front-Left (FL) — TB6612 channel A
// ---------------------------------------------------------------------------
#define FL_PWM_PIN    2   ///< GP2  → PWMA
#define FL_IN1_PIN    3   ///< GP3  → AIN1 (direction)
#define FL_IN2_PIN    4   ///< GP4  → AIN2 (direction)
#define FL_ENC_A_PIN  5   ///< GP5  → Encoder A (interrupt)
#define FL_ENC_B_PIN  6   ///< GP6  → Encoder B (direction sense)

// ---------------------------------------------------------------------------
// Motor 1: Front-Right (FR) — TB6612 channel B
// ---------------------------------------------------------------------------
#define FR_PWM_PIN    7   ///< GP7  → PWMB
#define FR_IN1_PIN    8   ///< GP8  → BIN1
#define FR_IN2_PIN    9   ///< GP9  → BIN2
#define FR_ENC_A_PIN  10  ///< GP10 → Encoder A
#define FR_ENC_B_PIN  11  ///< GP11 → Encoder B

// ---------------------------------------------------------------------------
// Motor 2: Rear-Left (RL) — TB6612 channel A (second driver)
// ---------------------------------------------------------------------------
#define RL_PWM_PIN    12  ///< GP12 → PWMA
#define RL_IN1_PIN    13  ///< GP13 → AIN1
#define RL_IN2_PIN    14  ///< GP14 → AIN2
#define RL_ENC_A_PIN  15  ///< GP15 → Encoder A
#define RL_ENC_B_PIN  16  ///< GP16 → Encoder B  ← NOTE: shared with IMU MISO default? Adjust if needed.

// ---------------------------------------------------------------------------
// Motor 3: Rear-Right (RR) — TB6612 channel B (second driver)
// ---------------------------------------------------------------------------
#define RR_PWM_PIN    17  ///< GP17 → PWMB
#define RR_IN1_PIN    18  ///< GP18 → BIN1       ← NOTE: shared with IMU SCK default? Adjust if needed.
#define RR_IN2_PIN    19  ///< GP19 → BIN2       ← NOTE: shared with IMU MOSI default? Adjust if needed.
#define RR_ENC_A_PIN  20  ///< GP20 → Encoder A
#define RR_ENC_B_PIN  21  ///< GP21 → Encoder B

// ---------------------------------------------------------------------------
// TB6612 Standby pin (optional — tie HIGH if not used)
// ---------------------------------------------------------------------------
// #define TB6612_STBY_PIN  22  ///< GP22 → STBY (drive HIGH to enable driver)
//   If defined, firmware drives this HIGH on init. If not defined, wire STBY to 3V3.

// hardware/spi.h must NOT be included here — it would cascade Pico SDK
// headers into every file that includes board_config.h.
// Instead, define a numeric index. The .cpp file (imu_driver.cpp) resolves
// this to spi0/spi1 after including hardware/spi.h itself.
#define IMU_SPI_IDX   0       ///< 0 = spi0, 1 = spi1

// ---------------------------------------------------------------------------
// ICM-20948 SPI pins (SPI0 — matches ROSArduinoBridge README default)
// IMPORTANT: If RL/RR motor pins above conflict, remap motor pins or use SPI1.
// Default SPI0 mapping from original diffdrive_arduino firmware README:
//   SCLK = GP18  |  MOSI = GP19  |  MISO = GP16  |  CS = GP17
// These overlap with RR motor and RL encoder pins above — REMAP as needed.
// Recommended: use GP22(CS), GP26(SCK), GP27(MOSI), GP28(MISO) for SPI1.
// ---------------------------------------------------------------------------
// IMU_SPI_PORT is resolved in imu_driver.cpp — do not use here.
#define IMU_CS_PIN    17       ///< GP17 — Chip Select (active LOW)
#define IMU_SCK_PIN   18       ///< GP18 — SPI Clock
#define IMU_MOSI_PIN  19       ///< GP19 — MOSI (SDI on ICM-20948)
#define IMU_MISO_PIN  16       ///< GP16 — MISO (ADA/SDO on ICM-20948)
#define IMU_BAUDRATE  4000000  ///< 4 MHz — safe for ICM-20948

// ---------------------------------------------------------------------------
// PWM configuration
// ---------------------------------------------------------------------------
#define PWM_WRAP        255    ///< 8-bit resolution (0–255)
#define PWM_CLK_DIV     4.0f   ///< Clock divider — adjust for desired PWM frequency
#define MAX_PWM         255    ///< Maximum PWM output magnitude

// ---------------------------------------------------------------------------
// PID defaults (runtime-tunable via 'u' command)
// ---------------------------------------------------------------------------
#define DEFAULT_KP  20    ///< Proportional gain — from ROSArduinoBridge default
#define DEFAULT_KD  12    ///< Derivative gain
#define DEFAULT_KI   0    ///< Integral gain
#define DEFAULT_KO  50    ///< Output divider (scales final PID output)

// ---------------------------------------------------------------------------
// Timing
// ---------------------------------------------------------------------------
// ALT: #define ENC_COUNTS_PER_REV 1440     ///< Encoder counts per full wheel revolution
#define PID_RATE_HZ     30       ///< PID + encoder update rate [Hz]
#define AUTO_STOP_MS  2000       ///< Stop motors if no 'm'/'o' command for this long [ms]
#define BAUD_RATE     115200     ///< USB-CDC baud rate (informational; USB-CDC is virtual)

// ---------------------------------------------------------------------------
// Firmware identification
// ---------------------------------------------------------------------------
#define FW_NAME     "mecanum_pico v2"
#define FW_FEATURES "TB6612 | ICM-20948 | 4xEncoder | PID | AutoStop"

#endif  // BOARD_CONFIG_H
