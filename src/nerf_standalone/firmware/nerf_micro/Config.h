#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

namespace Config {
        // Hardware Mapping
        // Pins: D2/D3 (ESCs), D9 (Shot), D10 (Tilt)
        const uint8_t PIN_FLY_L = 2;
        const uint8_t PIN_FLY_R = 3;
        const uint8_t PIN_SHOT = 9;
        const uint8_t PIN_TILT = 10;

        // --- ESC DIRECTION & RANGE ---
        // Falls ein Motor falsch herum dreht, hier auf 'true' setzen (erfordert
        // Bidirectional ESCs) Falls du Standard-ESCs hast: Zwei der drei Motorkabel
        // physisch tauschen!
        const bool INV_L = false;
        const bool INV_R = false;

        const uint16_t ESC_MIN = 1000;
        const uint16_t ESC_MAX = 2000;
        const uint16_t ESC_ARM = 1000; // Stillstand (bei Standard ESCs)
        const uint16_t ESC_MID = 1500; // Neutral (nur bei Bidirectional relevant)

        // --- SERVO RANGES ---
        const uint16_t SV_MIN_US = 500;
        const uint16_t SV_MAX_US = 2500;

        // --- TIMINGS ---
        const uint32_t ARM_DELAY_MS = 2000;
        const uint32_t SPINUP_MS = 1200;
        const uint32_t AUTO_DISARM_MS = 60000;

        // Deine kalibrierten Werte
        const uint16_t SHOT_NEUTRAL_DEFAULT = 1430;
        const uint32_t SHOT_DURATION_DEFAULT = 2520;
        const uint16_t SHOT_SPEED_OFFSET = 220;
        // Test-only Offset (stärkerer Ausschlag für reinen Pusher-Test)
        const uint16_t TEST_SHOT_OFFSET = 220;
        const uint16_t TILT_NEUTRAL_DEFAULT = 1430;
        // ZEIT: 2210ms | SPEED: 300 | NEUTRAL: 1430
        // ZEIT: 2520ms | SPEED: 220 | NEUTRAL: 1430

        // Brems-Parameter
        const uint16_t BRAKE_OFFSET = 600;
        const uint16_t BRAKE_MS = 15;

        const uint32_t BAUD_RATE = 115200;
} // namespace Config

#endif // CONFIG_H
