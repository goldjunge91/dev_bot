/**
 * NERF OS - SHOT CALIBRATION & HOMING SUITE
 * Hardware: Pro Micro (ATmega32U4)
 * Pins: D2/D3 (ESCs), D9 (Shot), D10 (Tilt)
 * Spec: 360° Servos (500-2500us)
 */

#include <Servo.h>

#define PIN_ESC_1 2
#define PIN_ESC_2 3
#define PIN_SHOT 9
#define PIN_TILT 10

Servo shotServo, tiltServo, esc1, esc2;

// --- Standardwerte ---
int shotNeutralUs = 1500;
int shotDurationMs = 500;
int tiltNeutralUs = 1500; // Neutralpunkt für Tilt (D10)
bool isArmed = false;

void setup() {
  Serial.begin(115200);

  // Warten auf Seriellen Monitor (Wichtig für Pro Micro)
  while (!Serial)
    ;

  // ESCs initialisieren
  esc1.attach(PIN_ESC_1, 1000, 2000);
  esc2.attach(PIN_ESC_2, 1000, 2000);
  esc1.writeMicroseconds(1000);
  esc2.writeMicroseconds(1000);

  delay(500);

  showHelp();
}

void showHelp() {
  Serial.println("\n=================================");
  Serial.println("--- NERF SHOT-CALIBRATOR READY ---");
  Serial.println("=================================");
  Serial.println("KALIBRIERUNG:");
  Serial.println("  NF             -> Nudge Forward (Winziger Schritt vor)");
  Serial.println(
      "  NB             -> Nudge Backward (Winziger Schritt zurueck)");
  Serial.println("  ZERO_S <us>    -> Nullpunkt (Stopp) suchen");
  Serial.println(
      "  SET_SHOT <ms>  -> Dauer fuer einen vollen Schuss festlegen");
  Serial.println("  UP <ms>        -> Launcher hochneigen");
  Serial.println("  DN <ms>        -> Launcher runterneigen");
  Serial.println("  ZERO_T <us>    -> Tilt-Stillstand suchen");
  Serial.println("  SAVE           -> Zeigt aktuelle Werte zum Notieren an");
  Serial.println("\nTEST & BETRIEB:");
  Serial.println("  TEST_SHOT <ms> -> Nur Pusher bewegen");
  Serial.println("  ARM / STOP     -> Flywheels scharf/aus");
  Serial.println("  SHOT           -> Feuer-Sequenz ausfuehren");
  Serial.println("  HELP           -> Diese Liste anzeigen");
  Serial.println("---------------------------------");
}

/**
 * Hilfsfunktion für Tilt-Bewegungen
 * @param speedUs: 500 (Ganz runter) bis 2500 (Ganz hoch)
 * @param duration: Wie lange die Bewegung dauern soll
 */
void moveTilt(int speedUs, int duration) {
  if (duration <= 0)
    return;
  tiltServo.attach(PIN_TILT, 500, 2500);
  tiltServo.writeMicroseconds(speedUs);
  delay(duration);
  tiltServo.writeMicroseconds(tiltNeutralUs);
  delay(50);
  tiltServo.detach();
  Serial.println("Tilt Bewegung abgeschlossen.");
}

// Hilfsfunktion für winzige Bewegungen (Nudge)
void nudgeShot(bool forward) {
  shotServo.attach(PIN_SHOT, 500, 2500);
  // Langsame Geschwindigkeit für Präzision
  int speed = forward ? (shotNeutralUs + 200) : (shotNeutralUs - 200);
  shotServo.writeMicroseconds(speed);
  delay(100); // Nur 100ms Impuls
  shotServo.writeMicroseconds(shotNeutralUs);
  delay(50);
  shotServo.detach();
  Serial.println("Nudge ausgeführt.");
}

// Die Kern-Funktion für die 360° Bewegung
void moveShot(int duration) {
  if (duration <= 0)
    return;
  Serial.print("Bewege Shot-Servo für ");
  Serial.print(duration);
  Serial.println("ms");

  shotServo.attach(PIN_SHOT, 500, 2500);
  shotServo.writeMicroseconds(2500); // Volle Kraft
  delay(duration);

  shotServo.writeMicroseconds(shotNeutralUs);
  delay(100);
  shotServo.detach();
}

void processCommand(String cmd) {
  cmd.trim();
  int spaceIndex = cmd.indexOf(' ');
  String action = (spaceIndex > -1) ? cmd.substring(0, spaceIndex) : cmd;
  action.toUpperCase();
  int val = (spaceIndex > -1) ? cmd.substring(spaceIndex + 1).toInt() : 0;

  // --- HOMING & NUDGE ---
  if (action == "NF") {
    nudgeShot(true);
  } else if (action == "NB") {
    nudgeShot(false);
  } else if (action == "SAVE") {
    Serial.println("\n--- AKTUELLE KALIBRIERUNG ---");
    Serial.print("ZERO_S (Shot Neutral): ");
    Serial.println(shotNeutralUs);
    Serial.print("ZERO_T (Tilt Neutral): ");
    Serial.println(tiltNeutralUs); // NEU
    Serial.print("SET_SHOT (Dauer): ");
    Serial.print(shotDurationMs);
    Serial.println(" ms");
    Serial.println("Notiere dir diese Werte!");
  }

  // --- KALIBRIERUNG & TEST ---
  else if (action == "TEST_SHOT") {
    moveShot(val > 0 ? val : 500);
  } else if (action == "HELP") {
    showHelp();
  } else if (action == "ZERO_S") {
    shotNeutralUs = val;
    shotServo.attach(PIN_SHOT, 500, 2500);
    shotServo.writeMicroseconds(shotNeutralUs);
    Serial.print("Test-Nullpunkt: ");
    Serial.println(shotNeutralUs);
  } else if (action == "SET_SHOT") {
    shotDurationMs = val;
    Serial.print("Schuss-Dauer gespeichert: ");
    Serial.print(shotDurationMs);
    Serial.println("ms");
  }
  // --- TILT STEUERUNG ---
  else if (action == "UP") {
    // Bewege hoch (2500us = Maximale Geschwindigkeit in eine Richtung)
    moveTilt(2500, val > 0 ? val : 200);
  } else if (action == "DN") {
    // Bewege runter (500us = Maximale Geschwindigkeit in die andere Richtung)
    moveTilt(500, val > 0 ? val : 200);
  } else if (action == "ZERO_T") {
    // Kalibrierung des Stillstands für Tilt
    tiltNeutralUs = val;
    tiltServo.attach(PIN_TILT, 500, 2500);
    tiltServo.writeMicroseconds(tiltNeutralUs);
    Serial.print("Tilt-Nullpunkt Test: ");
    Serial.println(tiltNeutralUs);
  }
  // --- BETRIEB ---
  else if (action == "ARM") {
    isArmed = true;
    Serial.println("ARMED - Flywheels bereit.");
  } else if (action == "SHOT") {
    if (!isArmed) {
      Serial.println("FEHLER: Erst ARM senden!");
      return;
    }

    int duration = (val > 0) ? val : shotDurationMs;
    esc1.writeMicroseconds(1500);
    esc2.writeMicroseconds(1500);
    delay(1200);
    moveShot(duration);
    esc1.writeMicroseconds(1000);
    esc2.writeMicroseconds(1000);
  } else if (action == "STOP" || action == "OFF") {
    isArmed = false;
    shotServo.detach();
    esc1.writeMicroseconds(1000);
    esc2.writeMicroseconds(1000);
    Serial.println("SYSTEM STOP / DISARMED");
  }
}

void loop() {
  if (Serial.available()) {
    processCommand(Serial.readStringUntil('\n'));
  }
}