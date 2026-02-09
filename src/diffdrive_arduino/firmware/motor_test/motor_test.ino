/***************************************************************
   MOTOR DIAGNOSTIC TEST v2
   
   Flash this to the Pico. Open Serial Monitor at 115200 baud.
   Follow the instructions on screen.
   
   WIRING:
     LEFT  motor: GP0 (PWM), GP4 (IN1), GP5 (IN2)  → TB6612
     RIGHT motor: GP2 (PWM), GP7 (IN1), GP8 (IN2)  → TB6612
     GP6 ist DEFEKT (nur 1.2V) - NICHT verwenden!
     
   TB6612 STBY must be connected to 3.3V!
   *************************************************************/

// === LEFT Motor (funktioniert) ===
#define L_PWM  0   // GP0
#define L_IN1  4   // GP4
#define L_IN2  5   // GP5

// === RIGHT Motor - GP6 DEFEKT, ersetzt durch GP2 ===
#define R_PWM  2   // GP2 (GP6 defekt, nur 1.2V!)
#define R_IN1  7   // GP7
#define R_IN2  8   // GP8

void stopAll() {
  digitalWrite(L_IN1, LOW);
  digitalWrite(L_IN2, LOW);
  digitalWrite(L_PWM, LOW);
  digitalWrite(R_IN1, LOW);
  digitalWrite(R_IN2, LOW);
  digitalWrite(R_PWM, LOW);
}

void setup() {
  Serial.begin(115200);
  delay(3000);
  
  Serial.println("==========================================");
  Serial.println("  MOTOR DIAGNOSTIC TEST v3");
  Serial.println("  RIGHT MOTOR: GP2(PWM), GP7(IN1), GP8(IN2)");
  Serial.println("==========================================");
  Serial.println();
  
  // --- PHASE 1: PIN VOLTAGE TEST ---
  // Jeder Pin wird einzeln HIGH geschaltet.
  // Miss mit Multimeter 3.3V am Pin.
  Serial.println("=== PHASE 1: PIN VOLTAGE TEST ===");
  Serial.println("Benutze ein Multimeter um Spannung an jedem Pin zu messen.");
  Serial.println("Jeder Pin bleibt 8 Sekunden HIGH.");
  Serial.println();
  
  int testPins[] = {L_PWM, L_IN1, L_IN2, R_PWM, R_IN1, R_IN2};
  const char* pinNames[] = {"GP0 (L_PWM)", "GP4 (L_IN1)", "GP5 (L_IN2)", 
                              "GP2 (R_PWM)", "GP7 (R_IN1)", "GP8 (R_IN2)"};
  
  // Init all as OUTPUT, all LOW
  for (int i = 0; i < 6; i++) {
    pinMode(testPins[i], OUTPUT);
    digitalWrite(testPins[i], LOW);
  }
  
  for (int i = 0; i < 6; i++) {
    Serial.print("  >>> ");
    Serial.print(pinNames[i]);
    Serial.println(" = HIGH (erwarte 3.3V) - 8 Sekunden...");
    digitalWrite(testPins[i], HIGH);
    delay(8000);
    digitalWrite(testPins[i], LOW);
    Serial.println("      -> LOW");
    delay(1000);
  }
  
  Serial.println();
  Serial.println("=== PHASE 2: MOTOR TESTS ===");
  delay(2000);
  
  // --- TEST A: RIGHT motor (GP2,7,8) ---
  Serial.println(">>> TEST A: RIGHT motor (GP2=HIGH, GP7=HIGH, GP8=LOW) - 4 sec");
  Serial.println("    Alle 3 Pins nur mit digitalWrite (kein analogWrite)");
  stopAll();
  digitalWrite(R_IN1, HIGH);  // GP7 HIGH
  digitalWrite(R_IN2, LOW);   // GP8 LOW  
  digitalWrite(R_PWM, HIGH);  // GP2 HIGH (full speed, no PWM)
  delay(4000);
  stopAll();
  Serial.println("    STOPPED");
  delay(2000);
  
  // --- TEST B: RIGHT motor with analogWrite PWM ---
  Serial.println(">>> TEST B: RIGHT motor (GP2=PWM200, GP7=HIGH, GP8=LOW) - 4 sec");
  stopAll();
  digitalWrite(R_IN1, HIGH);
  digitalWrite(R_IN2, LOW);
  analogWrite(R_PWM, 200);
  delay(4000);
  stopAll();
  analogWrite(R_PWM, 0);
  Serial.println("    STOPPED");
  delay(2000);
  
  // --- TEST C: Run RIGHT motor through LEFT motor pins ---
  // Steck den rechten Motor temporär auf die LINKEN TB6612 Ausgänge um!
  // Oder: Wir steuern den TB6612 Kanal B (links) an, an dem der linke Motor hängt
  Serial.println(">>> TEST C: LEFT motor channel (GP0=HIGH, GP4=HIGH, GP5=LOW) - 4 sec");
  Serial.println("    (Bestätigung dass linker Kanal funktioniert)");
  stopAll();
  digitalWrite(L_IN1, HIGH);
  digitalWrite(L_IN2, LOW);
  digitalWrite(L_PWM, HIGH);
  delay(4000);
  stopAll();
  Serial.println("    STOPPED");
  delay(2000);

  // --- TEST D: Drive RIGHT motor pins DIRECTLY with tight timing ---
  Serial.println(">>> TEST D: RIGHT motor - Pins einzeln setzen mit Pausen");
  stopAll();
  Serial.println("    1. GP7 (IN1) -> HIGH");
  digitalWrite(R_IN1, HIGH);
  delay(500);
  Serial.println("    2. GP8 (IN2) -> LOW (ist bereits LOW)");
  digitalWrite(R_IN2, LOW);
  delay(500);
  Serial.println("    3. GP2 (PWM) -> HIGH");
  digitalWrite(R_PWM, HIGH);
  Serial.println("    Motor sollte jetzt drehen! 5 Sekunden...");
  delay(5000);
  stopAll();
  Serial.println("    STOPPED");
  delay(2000);
  
  // --- TEST E: Use LEFT motor pins to drive the RIGHT TB6612 channel ---
  // Cross-test: Pico GP0,4,5 → TB6612 PWMA, AIN1, AIN2
  Serial.println(">>> TEST E: CROSS-TEST");
  Serial.println("    Wenn du kannst: Steck die Kabel von GP2,7,8 um auf GP0,4,5");
  Serial.println("    (rechten Motor an linke Pico-Pins haengen)");
  Serial.println("    Druecke dann Reset am Pico um den Test nochmal zu starten.");
  Serial.println();
  
  // --- TEST F: Try ALL possible GPIO combinations for right motor ---
  Serial.println(">>> TEST F: Brute force - GP2 als PWM, ALLE moeglichen IN1/IN2 Kombis");
  stopAll();
  
  // IN1=HIGH, IN2=LOW
  Serial.println("  F1: GP7=H, GP8=L, GP2=PWM200");
  digitalWrite(R_IN1, HIGH);
  digitalWrite(R_IN2, LOW);
  analogWrite(R_PWM, 200);
  delay(3000);
  stopAll(); analogWrite(R_PWM, 0);
  delay(1000);
  
  // IN1=LOW, IN2=HIGH  
  Serial.println("  F2: GP7=L, GP8=H, GP2=PWM200");
  digitalWrite(R_IN1, LOW);
  digitalWrite(R_IN2, HIGH);
  analogWrite(R_PWM, 200);
  delay(3000);
  stopAll(); analogWrite(R_PWM, 0);
  delay(1000);
  
  // Both HIGH (brake mode with PWM)
  Serial.println("  F3: GP7=H, GP8=H, GP2=PWM200 (short brake)");
  digitalWrite(R_IN1, HIGH);
  digitalWrite(R_IN2, HIGH);
  analogWrite(R_PWM, 200);
  delay(3000);
  stopAll(); analogWrite(R_PWM, 0);
  delay(1000);
  
  // --- DONE ---
  Serial.println();
  Serial.println("==========================================");
  Serial.println("  ALLE TESTS FERTIG");
  Serial.println("==========================================");
  Serial.println();
  Serial.println("FRAGEN:");
  Serial.println("  Phase 1: Hattest du bei JEDEM Pin 3.3V gemessen?");
  Serial.println("           Besonders GP2, GP7, GP8?");
  Serial.println("  Test A:  Drehte der rechte Motor? (rein digital)");
  Serial.println("  Test B:  Drehte der rechte Motor? (PWM)");
  Serial.println("  Test C:  Drehte der linke Motor? (Kontrolle)");
  Serial.println("  Test D:  Drehte der rechte Motor? (langsam geschaltet)");
  Serial.println("  Test F:  Drehte bei F1, F2 oder F3 etwas?");
  Serial.println();
  Serial.println("  Wenn KEIN rechter Motor-Test funktioniert:");
  Serial.println("  -> Problem ist TB6612 Eingangsseite oder Verkabelung!");
  Serial.println("  -> Pruefe: STBY an 3.3V? VM an Motorspannung?");
  Serial.println("  -> Pruefe: Sind GP2,GP7,GP8 tatsaechlich an PWMA,AIN1,AIN2?");
  Serial.println("  -> Tausche testweise L/R Kabel am TB6612 INPUT");
}

void loop() {
  // Nothing
}
