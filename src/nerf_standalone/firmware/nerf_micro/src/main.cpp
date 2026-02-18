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

#include <Arduino.h>
#include "../include/Config.h"
#include "Launcher.h"
#include "TiltController.h"
#include "Comms.h"


// --- OBJECTS ---
Launcher nerf;
TiltController tiltCtrl(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);

// Comms now takes both objects
Comms commsUSB(nerf, tiltCtrl, Serial);
Comms commsUART(nerf, tiltCtrl, Serial1);

// --- GLOBALE AUSGABE-HELFER ---
void globalPrint(const __FlashStringHelper *msg) {
  Serial.println(msg);
  Serial1.println(msg);
}

void globalPrintf(const char *format, long value) {
  char buf[64];
  sprintf(buf, format, value);
  Serial.println(buf);
  Serial1.println(buf);
}

void printHelp() {
  globalPrint(F("\n--- COMMAND LIST ---"));
  globalPrint(F(" [ SYSTEM ]"));
  globalPrint(F(" > ARM / STOP / STATUS   - Flywheel & Safety"));
  globalPrint(F(" > SAVE                  - Show Current Config"));
  globalPrint(F(" [ FIRING ]"));
  globalPrint(F(" > SHOT <pwr>            - Fire (0-100)"));
  globalPrint(F(" > TEST_ESC <pwr>        - Flywheels Only"));
  globalPrint(F(" > PWM <us>              - Manual ESC Signal"));
  globalPrint(F(" > CAL                   - Calibrate ESCs"));
  globalPrint(F(" > TEST_SHOT <ms>        - Pusher Cycle Only"));
  globalPrint(F(" > NF / NB               - Nudge Pusher"));
  globalPrint(F(" [ TILT ]"));
  globalPrint(F(" > UP / DN <ms>          - Move Tilt"));
  globalPrint(F(" > ZERO_S / ZERO_T       - Set Neutrals"));
  globalPrint(F("--------------------\n"));
}

void printConfig() {
  globalPrint(F("\n--- CURRENT CONFIG ---"));
  // Zugriff über Getter-Funktionen der Klassen
  globalPrintf("Shot Zero:     %ld us", (long)nerf.getShotZero());
  globalPrintf("Tilt Zero:     %ld us", (long)tiltCtrl.getNeutral());
  globalPrintf("Shot Duration: %ld ms", (long)nerf.getShotDur());
  globalPrint(F("----------------------"));
}

void printStartup() {
  globalPrint(F("================================"));
  globalPrint(F("      NERF OS PRO ONLINE        "));
  globalPrint(F("================================"));
  globalPrintf("Baudrate:      %ld", (long)Config::BAUD_RATE);
  printConfig();
  globalPrint(F("Type 'HELP' for commands."));
  globalPrint(F("================================\n"));
}

// --- SETUP ---
void setup() {
  Serial.begin(Config::BAUD_RATE);
  Serial1.begin(Config::BAUD_RATE);
  // Kurzer Sicherheits-Check für USB
  uint32_t startWait = millis();
  while (!Serial && millis() - startWait < 2000)
    ;

  // FLUSH BUFFER: Clear any old commands (e.g. from ROS buffered write)
  while (Serial.available())
    Serial.read();
  while (Serial1.available())
    Serial1.read();

  pinMode(LED_BUILTIN, OUTPUT);
  // Blink 3 times to signal ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
  nerf.begin();
  printStartup();
}

// --- LOOP ---
void loop() {
  nerf.update();
  tiltCtrl.update();
  commsUSB.update();
  commsUART.update();
}