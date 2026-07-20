/**
 * NERF OS PRO - Modular Version
 *
 * Overview:
 * - Config.h:   Settings & Pins
 * - Launcher.h: Core Logic (Servos, ESCs, State Machine)
 * - Comms.h:    Communication (USB/UART)
 * - Tilt.h:     Tilt logic (Decoupled)
 *
 * This file is the entry point.
 */

#include "../include/Config.h"
#include "Comms.h"
// #include "ESCCalibration.h"  // Include Debug Class
#include "Help.h"
#include "Launcher.h"
#include "SerialOutput.h"
#include "TiltController.h"

#include <Arduino.h>

// #define DEBUG_CALIBRATION

// --- OBJECTS ---
// Global instances for the main subsystems
Launcher nerf;
TiltController tiltCtrl(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);

// Comms now takes both objects
// Listen on both USB (Serial) and UART (Serial1)
Comms commsUSB(nerf, tiltCtrl, Serial);
Comms commsUART(nerf, tiltCtrl, Serial1);

// USB-Verbindungsstatus (DTR) — fuer das Connect-Banner in loop()
static bool usbWasConnected = false;

// --- SETUP ---
void setup() {
    Serial.begin(Config::BAUD_RATE);
    Serial1.begin(Config::BAUD_RATE);

    // Wait for USB Serial to become available (with timeout)
    // This ensures we don't miss boot messages if a terminal is attached.
    uint32_t startWait = millis();
    while (!Serial && millis() - startWait < 2000);

    // FLUSH BUFFER: Clear any old commands (e.g. from ROS buffered write)
    while (Serial.available()) Serial.read();
    while (Serial1.available()) Serial1.read();

    pinMode(LED_BUILTIN, OUTPUT);
    // Blink 3 times to signal ready status to the user
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(100);
        digitalWrite(LED_BUILTIN, LOW);
        delay(100);
    }

    // Initialize hardware (Safing everything)
    nerf.begin();
    Help::printStartup(nerf.getShotZero(), tiltCtrl.getNeutral(), nerf.getShotDur());
    // War beim Boot schon ein Monitor offen, nicht direkt in loop() nochmal drucken
    usbWasConnected = (bool)Serial;
}

// --- LOOP ---
/**
 * @brief Main execution loop.
 *
 * 1. Updates Firing FSM (State transitions, Hardware control)
 * 2. Updates Tilt Controller (Timed detach logic)
 * 3. Checks for new commands on USB and UART
 */
void loop() {
    // Banner bei jedem neuen USB-Connect (DTR rising edge). Der 32u4 resettet
    // beim Oeffnen des Monitors NICHT (anders als ein UNO) — ohne dies bleibt
    // ein nach dem Boot geoeffneter Monitor stumm und die Firmware wirkt tot.
    // Die ROS2-Seite liest nie vom Serial (write-only), Banner stoert sie nicht.
    bool usbConnected = (bool)Serial;
    if (usbConnected && !usbWasConnected) {
        Help::printStartup(nerf.getShotZero(), tiltCtrl.getNeutral(), nerf.getShotDur());
    }
    usbWasConnected = usbConnected;

    nerf.update();
    tiltCtrl.update();
    commsUSB.update();
    commsUART.update();
}
