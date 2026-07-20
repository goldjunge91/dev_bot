//
// Created by tozzi on 18.02.2026.
//

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
// #include <cstdint>

namespace Config {
// Hardware Mapping
const uint8_t PIN_ESC_LEFT = 2;
const uint8_t PIN_ESC_RIGHT = 3;
const uint8_t PIN_SHOT = 9;
const uint8_t PIN_TILT = 10;

// --- ESC RANGE ---
const uint16_t ESC_MIN = 1000;
const uint16_t ESC_MAX = 2000;
const uint16_t ESC_ARM = 1000;

// --- SERVO RANGES ---
const uint16_t SV_MIN_US = 500;
const uint16_t SV_MAX_US = 2500;

// --- TIMINGS ---
const uint32_t ARM_DELAY_MS = 2000;
const uint32_t SPINUP_MS = 1200;
const uint32_t AUTO_DISARM_MS = 60000;
// T_POS Haltezeit vor dem Auto-Detach (5-10s Fenster fuer manuelles Tuning, dann
// Sicherheits-Release)
const uint32_t TILT_HOLD_MS = 8000;

// Deine kalibrierten Werte
const uint16_t SHOT_NEUTRAL_DEFAULT = 1430;
const uint32_t SHOT_DURATION_DEFAULT = 2520;
const uint16_t SHOT_SPEED_OFFSET = 220;
const uint16_t TEST_SHOT_OFFSET = 220;
const uint16_t TILT_NEUTRAL_DEFAULT = 1430;

// Brems-Parameter
const uint16_t BRAKE_OFFSET = 600;
const uint16_t BRAKE_MS = 15;
const uint16_t COOLDOWN_TIME = 2;

const uint32_t BAUD_RATE = 115200;
}  // namespace Config

#endif  // CONFIG_H
