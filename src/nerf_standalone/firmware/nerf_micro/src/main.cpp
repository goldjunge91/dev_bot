/**
 * NERF OS PRO - Modular Version
 *
 * Overview:
 * - Config.h:   Settings & Pins
 * - Launcher.h: Core Logic (Servos, ESCs, State Machine)
 * - Comms.h:    Communication (USB/UART)
 * - Tilt.h:     Tilt logic
 *
 * This file is the entry point.
 */

#include "Comms.h"
#include "Config.h"
#include "Launcher.h"
#include "SerialOutput.h"
#include "TiltController.h"
#include <Arduino.h>

// --- OBJECTS ---
// Global instances for the main subsystems
Launcher nerf;
TiltController tiltCtrl(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);

// Comms now takes both objects
// Listen on both USB (Serial) and UART (Serial1)
Comms commsUSB(nerf, tiltCtrl, Serial);
Comms commsUART(nerf, tiltCtrl, Serial1);

void printHelp() {
  SerialOutput::print(F("\n--- COMMAND LIST ---"));
  SerialOutput::print(F(" [ SYSTEM ]"));
  SerialOutput::print(F(" > ARM / STOP / STATUS   - Flywheel & Safety"));
  SerialOutput::print(F(" > SAVE                  - Show Current Config"));
  SerialOutput::print(F(" [ FIRING ]"));
  SerialOutput::print(F(" > SHOT <pwr>            - Fire (0-100)"));
  SerialOutput::print(F(" > TEST_ESC <pwr>        - Flywheels Only"));
  SerialOutput::print(F(" > PWM <us>              - Manual ESC Signal"));
  SerialOutput::print(F(" > CAL                   - Calibrate ESCs"));
  SerialOutput::print(F(" > TEST_SHOT <ms>        - Pusher Cycle Only"));
  SerialOutput::print(F(" > NF / NB               - Nudge Pusher"));
  SerialOutput::print(F(" [ TILT ]"));
  SerialOutput::print(F(" > UP / DN <ms>          - Move Tilt"));
  SerialOutput::print(F(" > ZERO_S / ZERO_T       - Set Neutrals"));
  SerialOutput::print(F("--------------------\n"));
}

void printConfig() {
  SerialOutput::print(F("\n--- CURRENT CONFIG ---"));
  SerialOutput::printf("Shot Zero:     %ld us", (long)nerf.getShotZero());
  SerialOutput::printf("Tilt Zero:     %ld us", (long)tiltCtrl.getNeutral());
  SerialOutput::printf("Shot Duration: %ld ms", (long)nerf.getShotDur());
  SerialOutput::print(F("----------------------"));
}

void printStartup() {
  SerialOutput::print(F("================================"));
  SerialOutput::print(F("      NERF OS PRO ONLINE        "));
  SerialOutput::print(F("================================"));
  SerialOutput::printf("Baudrate:      %ld", (long)Config::BAUD_RATE);
  printConfig();
  SerialOutput::print(F("Type 'HELP' for commands."));
  SerialOutput::print(F("================================\n"));
}

// --- SETUP ---
void setup() {
  Serial.begin(Config::BAUD_RATE);
  Serial1.begin(Config::BAUD_RATE);

  // Wait for USB Serial to become available (with timeout)
  // This ensures we don't miss boot messages if a terminal is attached.
  uint32_t startWait = millis();
  while (!Serial && millis() - startWait < 2000)
    ;

  // FLUSH BUFFER: Clear any old commands (e.g. from ROS buffered write)
  while (Serial.available())
    Serial.read();
  while (Serial1.available())
    Serial1.read();

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
  printStartup();
}

// --- LOOP ---
// --- LOOP ---
/**
 * @brief Main execution loop.
 *
 * 1. Updates Firing FSM (State transitions, Hardware control)
 * 2. Updates Tilt Controller (Timed detach logic)
 * 3. Checks for new commands on USB and UART
 */
void loop() {
  nerf.update();
  tiltCtrl.update();
  commsUSB.update();
  commsUART.update();
}