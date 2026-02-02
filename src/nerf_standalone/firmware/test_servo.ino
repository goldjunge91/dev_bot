#include <Servo.h>

const int PIN_SHOT = 9;
Servo shotServo;

// Deine ermittelten Bestwerte
int neutralUs = 1430;
int testDuration = 2210;
int speedOffset = 300;

void setup() {
  Serial.begin(115200);
  while (!Serial)
    ;
  Serial.println(F("=== PRÄZISIONS-TOOL V2 ==="));
  Serial.println(F("Steuerung:"));
  Serial.println(F("  >  -> Kleiner Schritt VORWÄRTS"));
  Serial.println(F("  <  -> Kleiner Schritt RÜCKWÄRTS"));
  Serial.println(F("  T  -> TEST-UMDREHUNG (1 Voller Zyklus)"));
  Serial.println(F("  + / - -> Zeit anpassen"));
  Serial.println(F("  * / / -> Speed anpassen"));
  printStatus();
}

void printStatus() {
  Serial.print(F("ZEIT: "));
  Serial.print(testDuration);
  Serial.print(F("ms | SPEED: "));
  Serial.print(speedOffset);
  Serial.print(F(" | NEUTRAL: "));
  Serial.println(neutralUs);
}

// Die "Nudge" Funktion für Millimeter-Arbeit
void nudge(bool forward) {
  shotServo.attach(PIN_SHOT, 500, 2500);
  // Wir nudgen extra langsam (Offset 150), damit du nicht übers Ziel
  // hinaustiffst
  int nudgeSpeed = forward ? (neutralUs + 150) : (neutralUs - 150);
  shotServo.writeMicroseconds(nudgeSpeed);
  delay(40); // Nur ein extrem kurzer Impuls
  shotServo.writeMicroseconds(neutralUs);
  delay(20);
  shotServo.detach();
}

void runTest() {
  shotServo.attach(PIN_SHOT, 500, 2500);
  int moveSpeed = neutralUs + speedOffset;

  Serial.println(F("Zyklus startet..."));
  shotServo.writeMicroseconds(moveSpeed);

  // Wir fahren 10ms kürzer als geplant...
  delay(testDuration - 10);

  // --- AKTIVE BREMSE ---
  // Wir geben für 15ms kurz "Vollgas Rückwärts"
  shotServo.writeMicroseconds(neutralUs - 600);
  delay(15);

  // Jetzt erst auf Neutral und Detach
  shotServo.writeMicroseconds(neutralUs);
  delay(50);
  shotServo.detach();

  Serial.println(F("Zyklus mit Bremse beendet."));
}
void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '>')
      nudge(true);
    if (c == '<')
      nudge(false);
    if (c == 'T' || c == 't')
      runTest();
    if (c == '+')
      testDuration += 10;
    if (c == '-')
      testDuration -= 10;
    if (c == '*')
      speedOffset += 20;
    if (c == '/')
      speedOffset -= 20;

    if (c == '>' || c == '<' || c == '+' || c == '-' || c == '*' || c == '/') {
      printStatus();
    }
  }
}