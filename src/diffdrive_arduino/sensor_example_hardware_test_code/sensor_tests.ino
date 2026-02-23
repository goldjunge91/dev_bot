// void setup() {
//   // Serielle Kommunikation für die Ausgabe starten
//   Serial.begin(115200);
//   while (!Serial) {
//     delay(10); // Warten, bis der serielle Port bereit ist
//   }
//   Serial.println("Hallo, Welt! Die serielle Verbindung funktioniert.");
// }

// void loop() {
//   Serial.println("Ich sende Daten...");
//   delay(1000);
// }

// #include <Wire.h>

// // I2C-Adressen und Register des ICM-20948
// constexpr uint8_t ICM_ADDR_DEFAULT = 0x68;  // Adresse, wenn der AD0-Pin mit GND verbunden ist
// constexpr uint8_t ICM_ADDR_ALT     = 0x69;  // Adresse, wenn der AD0-Pin mit VCC (3.3V) verbunden ist
// constexpr uint8_t REG_WHO_AM_I     = 0x00;  // Register zur Identifikation des Sensors
// constexpr uint8_t EXPECTED_ID      = 0xEA;  // Der Wert, den der Sensor zurückgeben sollte

// /**
//  * @brief Liest das WHO_AM_I-Register von einer gegebenen I2C-Adresse aus.
//  * @param address Die zu prüfende I2C-Adresse.
//  */
// void scanAddress(uint8_t address) {
//   // Beginne die Übertragung zur angegebenen Adresse
//   Wire.beginTransmission(address);
//   // Sage dem Sensor, welches Register wir lesen wollen
//   Wire.write(REG_WHO_AM_I);
  
//   // Beende die Übertragung und prüfe auf Fehler.
//   // Ein Rückgabewert != 0 bedeutet, dass kein Gerät geantwortet hat.
//   if (Wire.endTransmission(false) != 0) {
//     Serial.print("Kein Gerät antwortet auf Adresse 0x");
//     Serial.println(address, HEX);
//     return; // Funktion hier beenden
//   }

//   // Fordere genau ein Byte vom Sensor an
//   Wire.requestFrom(address, static_cast<uint8_t>(1));
  
//   // Prüfe, ob Daten verfügbar sind
//   if (Wire.available()) {
//     // Lese das Byte aus und gib es aus
//     uint8_t whoami = Wire.read();
//     Serial.print("Adresse 0x");
//     Serial.print(address, HEX);
//     Serial.print(" -> WHO_AM_I = 0x");
//     Serial.println(whoami, HEX);

//     // Überprüfen, ob die ID korrekt ist
//     if (whoami == EXPECTED_ID) {
//       Serial.println(">>> Erfolg! Sensor ICM-20948 erkannt.");
//     } else {
//       Serial.println(">>> Unerwartete ID. Falscher Sensor oder Verkabelungsfehler?");
//     }
//   } else {
//     Serial.print("Keine Daten von 0x");
//     Serial.println(address, HEX);
//   }
// }

// void setup() {
//   // 1. Serielle Kommunikation starten und warten
//   Serial.begin(115200);
//   while (!Serial) {
//     delay(10); 
//   }
//   Serial.println("\n--- ICM-20948 Sensor-Test ---");

//   // 2. I2C-Kommunikation auf den Pins GP16 (SCL) und GP17 (SDA) initialisieren
//   Wire.setSDA(17);
//   Wire.setSCL(16);
//   Wire.begin();
//   Wire.setClock(100000); // 100 kHz ist eine sichere I2C-Standardgeschwindigkeit
// }

// void loop() {
//   Serial.println("\n---- Neuer Scan ----");
  
//   // Beide möglichen Adressen nacheinander scannen
//   scanAddress(ICM_ADDR_DEFAULT);
//   scanAddress(ICM_ADDR_ALT);
  
//   delay(2000);  // Alle 2 Sekunden wiederholen
// }


// #include <Wire.h>

// // Die I2C-Adresse des Sensors (AD0 an GND)
// constexpr uint8_t ICM_ADDR = 0x68;

// // Wichtige Register des ICM-20948
// // User Bank 0 Register
// constexpr uint8_t REG_WHO_AM_I     = 0x00;
// constexpr uint8_t EXPECTED_ID      = 0xEA;
// constexpr uint8_t REG_USER_CTRL      = 0x03;
// constexpr uint8_t REG_PWR_MGMT_1     = 0x06;
// constexpr uint8_t REG_ACCEL_XOUT_H   = 0x2D;
// constexpr uint8_t REG_GYRO_XOUT_H    = 0x33;
// constexpr uint8_t REG_TEMP_OUT_H     = 0x39;

// // Wir verwenden 16-Bit-Integer mit Vorzeichen, um die Rohdaten zu speichern
// int16_t accel_x, accel_y, accel_z;
// int16_t gyro_x, gyro_y, gyro_z;
// int16_t temperature;

// void setup() {
//   // 1. Serielle Kommunikation starten
//   Serial.begin(115200);
//   while (!Serial) {
//     delay(10); 
//   }
//   Serial.println("\n--- ICM-20948 Rohdaten-Leser ---");

//   // 2. I2C-Kommunikation initialisieren
//   Wire.setSDA(17);
//   Wire.setSCL(16);
//   Wire.begin();
//   Wire.setClock(400000); // Man kann die Geschwindigkeit für schnellere Datenübertragung erhöhen

//   // 3. Sensor-Identität prüfen
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_WHO_AM_I);
//   Wire.endTransmission(false);
//   Wire.requestFrom(ICM_ADDR, 1);
//   uint8_t whoami = Wire.read();

//   if (whoami == EXPECTED_ID) {
//     Serial.println("ICM-20948 erkannt.");
//   } else {
//     Serial.print("Fehler: Unerwartete ID 0x");
//     Serial.println(whoami, HEX);
//     Serial.println("Programm wird angehalten. Verkabelung prüfen!");
//     while (1); // Endlosschleife bei Fehler
//   }
  
//   // 4. Sensor aus dem Schlafmodus holen
//   // Das ist ein SEHR WICHTIGER Schritt!
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_PWR_MGMT_1);
//   Wire.write(0x01); // Wählt automatisch die beste Taktquelle, um den Sensor zu aktivieren
//   Wire.endTransmission();
  
//   Serial.println("Sensor aktiviert. Beginne Messung...");
//   delay(100);
// }

// void loop() {
//   // --- Beschleunigungsmesser-Daten lesen ---
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_ACCEL_XOUT_H); // Startregister
//   Wire.endTransmission(false);
//   Wire.requestFrom(ICM_ADDR, 6); // 6 Bytes anfordern (X, Y, Z je 2 Bytes)

//   // Die Daten kommen als High-Byte und Low-Byte. Wir müssen sie kombinieren.
//   accel_x = (Wire.read() << 8) | Wire.read();
//   accel_y = (Wire.read() << 8) | Wire.read();
//   accel_z = (Wire.read() << 8) | Wire.read();

//   // --- Gyroskop-Daten lesen ---
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_GYRO_XOUT_H); // Startregister
//   Wire.endTransmission(false);
//   Wire.requestFrom(ICM_ADDR, 6); // 6 Bytes anfordern

//   gyro_x = (Wire.read() << 8) | Wire.read();
//   gyro_y = (Wire.read() << 8) | Wire.read();
//   gyro_z = (Wire.read() << 8) | Wire.read();

//   // --- Temperatur-Daten lesen ---
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_TEMP_OUT_H); // Startregister
//   Wire.endTransmission(false);
//   Wire.requestFrom(ICM_ADDR, 2); // 2 Bytes anfordern

//   temperature = (Wire.read() << 8) | Wire.read();

//   // --- Daten formatiert ausgeben ---
//   Serial.print("Accel (X,Y,Z): ");
//   Serial.print(accel_x);
//   Serial.print(", ");
//   Serial.print(accel_y);
//   Serial.print(", ");
//   Serial.print(accel_z);

//   Serial.print("  |  Gyro (X,Y,Z): ");
//   Serial.print(gyro_x);
//   Serial.print(", ");
//   Serial.print(gyro_y);
//   Serial.print(", ");
//   Serial.print(gyro_z);
  
//   // Die Roh-Temperatur muss noch umgerechnet werden
//   // Formel laut Datenblatt: Temp in °C = (TEMP_OUT / 333.87) + 21.0
//   float temp_c = (temperature / 333.87) + 21.0;
//   Serial.print("  |  Temp: ");
//   Serial.print(temp_c);
//   Serial.println(" C");

//   delay(100); // 10 mal pro Sekunde ausgeben
// }


// #include <Wire.h>

// // I2C-Adresse und Register
// constexpr uint8_t ICM_ADDR = 0x68;
// constexpr uint8_t REG_WHO_AM_I = 0x00;
// constexpr uint8_t EXPECTED_ID = 0xEA;
// constexpr uint8_t REG_PWR_MGMT_1 = 0x06;

// void setup() {
//   // 1. Serielle Kommunikation starten
//   Serial.begin(115200);
//   while (!Serial) {
//     delay(10);
//   }
//   Serial.println("\n--- ICM-20948 Rohdaten-Leser (Diagnose-Modus) ---");

//   // 2. I2C-Kommunikation initialisieren
//   Serial.println("Initialisiere I2C...");
//   Wire.setSDA(17);
//   Wire.setSCL(16);
//   Wire.begin();
//   Wire.setClock(100000); // Eine langsamere, sicherere Geschwindigkeit für den Test
//   Serial.println("I2C initialisiert.");

//   // 3. Sensor-Identität prüfen
//   Serial.println("Prüfe Sensor-Identität...");
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_WHO_AM_I);
  
//   // Prüfen, ob ein Gerät auf die Adresse reagiert
//   byte error = Wire.endTransmission(false);
//   if (error != 0) {
//     Serial.print("FEHLER: Kein Gerät antwortet auf Adresse 0x68. Fehlercode: ");
//     Serial.println(error);
//     Serial.println("Programm wird angehalten. Verkabelung prüfen!");
//     while (1);
//   }
  
//   Wire.requestFrom(ICM_ADDR, 1);
//   if (!Wire.available()) {
//       Serial.println("FEHLER: Keine Daten vom Sensor erhalten nach Adressierung.");
//       Serial.println("Programm wird angehalten. Verkabelung prüfen!");
//       while (1);
//   }
//   uint8_t whoami = Wire.read();

//   if (whoami == EXPECTED_ID) {
//     Serial.println("Sensor-Identität OK (0xEA).");
//   } else {
//     Serial.print("FEHLER: Unerwartete ID 0x");
//     Serial.println(whoami, HEX);
//     Serial.println("Programm wird angehalten. Falschen Sensor angeschlossen?");
//     while (1);
//   }
  
//   // 4. Sensor aus dem Schlafmodus holen
//   Serial.println("Aktiviere Sensor (PWR_MGMT_1)...");
//   Wire.beginTransmission(ICM_ADDR);
//   Wire.write(REG_PWR_MGMT_1);
//   Wire.write(0x01);
//   error = Wire.endTransmission();

//   if (error != 0) {
//     Serial.print("FEHLER beim Senden des Aktivierungsbefehls. Fehlercode: ");
//     Serial.println(error);
//     Serial.println("Programm wird angehalten.");
//     while(1);
//   }
  
//   Serial.println("Sensor erfolgreich aktiviert. Setup abgeschlossen.");
//   delay(100);
// }

// void loop() {
//   // Dieser Teil wird erst erreicht, wenn setup() komplett durchläuft
//   Serial.println("Beginne Messung im Loop...");
//   delay(2000);
// }

// #include <SPI.h>

// // Pin-Definitionen für SPI
// // MISO, MOSI, SCK werden von der SPI-Bibliothek auf den Standard-Pins (GP16, 19, 18) verwaltet
// constexpr uint8_t CS_PIN = 17; // Chip Select auf GP17

// // Register des ICM-20948
// constexpr uint8_t REG_WHO_AM_I     = 0x00;
// constexpr uint8_t EXPECTED_ID      = 0xEA;
// constexpr uint8_t REG_PWR_MGMT_1     = 0x06;
// constexpr uint8_t REG_ACCEL_XOUT_H   = 0x2D;
// constexpr uint8_t REG_GYRO_XOUT_H    = 0x33;
// constexpr uint8_t REG_TEMP_OUT_H     = 0x39;
// constexpr uint8_t REG_USER_BANK_SEL  = 0x7F; // Register zum Bank-Wechsel

// // Globale Variablen für Rohdaten
// int16_t accel_x, accel_y, accel_z;
// int16_t gyro_x, gyro_y, gyro_z;
// int16_t temperature;

// // --- SPI Hilfsfunktionen ---

// /**
//  * @brief Schreibt ein einzelnes Byte in ein Sensor-Register über SPI.
//  */
// void spi_write_register(uint8_t reg, uint8_t data) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0)); // 1 MHz, MSB first, Mode 0
//   digitalWrite(CS_PIN, LOW);   // Chip Select aktivieren
//   SPI.transfer(reg & 0x7F);    // Register-Adresse senden (R/W-Bit = 0 für Schreiben)
//   SPI.transfer(data);          // Daten senden
//   digitalWrite(CS_PIN, HIGH);  // Chip Select deaktivieren
//   SPI.endTransaction();
// }

// /**
//  * @brief Liest mehrere Bytes von aufeinanderfolgenden Sensor-Registern über SPI.
//  */
// void spi_read_registers(uint8_t start_reg, uint8_t* buffer, uint8_t count) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(start_reg | 0x80); // Register-Adresse senden (R/W-Bit = 1 für Lesen)
//   for (uint8_t i = 0; i < count; i++) {
//     buffer[i] = SPI.transfer(0x00); // Dummy-Byte senden, um ein Byte zu empfangen
//   }
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
// }

// void setup() {
//   Serial.begin(115200);
//   while (!Serial) {
//     delay(10);
//   }
//   Serial.println("\n--- ICM-20948 Rohdaten-Leser (SPI-Modus) ---");

//   // Chip Select Pin initialisieren
//   pinMode(CS_PIN, OUTPUT);
//   digitalWrite(CS_PIN, HIGH); // Sensor ist anfangs nicht ausgewählt

//   // SPI-Bus starten
//   SPI.begin();

//   // Sensor-Identität prüfen
//   uint8_t whoami;
//   spi_read_registers(REG_WHO_AM_I, &whoami, 1);

//   if (whoami == EXPECTED_ID) {
//     Serial.println("ICM-20948 via SPI erkannt.");
//   } else {
//     Serial.print("Fehler: Unerwartete ID 0x");
//     Serial.println(whoami, HEX);
//     Serial.println("Programm wird angehalten. Verkabelung prüfen!");
//     while (1);
//   }

//   // Sensor aus dem Schlafmodus holen
//   spi_write_register(REG_PWR_MGMT_1, 0x01);
//   Serial.println("Sensor aktiviert. Beginne Messung...");
//   delay(100);
//  // Warten, bis der Computer (Python) ein Zeichen sendet
//   while (Serial.available() == 0) {
//     delay(10); // Kurz warten und erneut prüfen
//   }
//   // Eingehendes Zeichen aus dem Puffer lesen und verwerfen
//   Serial.read();
  
//   // Jetzt, da wir wissen, dass Python zuhört, senden wir den Header
//   Serial.println("Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_C");
// }


// void loop() {
//   uint8_t buffer[6]; // Puffer zum Empfangen der Daten

//   // Beschleunigungsmesser-Daten lesen
//   spi_read_registers(REG_ACCEL_XOUT_H, buffer, 6);
//   accel_x = (buffer[0] << 8) | buffer[1];
//   accel_y = (buffer[2] << 8) | buffer[3];
//   accel_z = (buffer[4] << 8) | buffer[5];

//   // Gyroskop-Daten lesen
//   spi_read_registers(REG_GYRO_XOUT_H, buffer, 6);
//   gyro_x = (buffer[0] << 8) | buffer[1];
//   gyro_y = (buffer[2] << 8) | buffer[3];
//   gyro_z = (buffer[4] << 8) | buffer[5];

//   // Temperatur-Daten lesen
//   spi_read_registers(REG_TEMP_OUT_H, buffer, 2);
//   temperature = (buffer[0] << 8) | buffer[1];

//  Serial.print(accel_x);
//   Serial.print(",");
//   Serial.print(accel_y);
//   Serial.print(",");
//   Serial.print(accel_z);
//   Serial.print(",");
//   Serial.print(gyro_x);
//   Serial.print(",");
//   Serial.print(gyro_y);
//   Serial.print(",");
//   Serial.print(gyro_z);
//   Serial.print(",");
//   float temp_c = (temperature / 333.87) + 21.0;
//   Serial.println(temp_c);

//   delay(100);
// }


// #include <SPI.h>

// // Pin-Definitionen für SPI
// constexpr uint8_t CS_PIN = 17; // Chip Select auf GP17

// // Register des ICM-20948
// constexpr uint8_t REG_WHO_AM_I     = 0x00;
// constexpr uint8_t EXPECTED_ID      = 0xEA;
// constexpr uint8_t REG_PWR_MGMT_1     = 0x06;
// constexpr uint8_t REG_ACCEL_XOUT_H   = 0x2D;
// constexpr uint8_t REG_GYRO_XOUT_H    = 0x33;
// constexpr uint8_t REG_TEMP_OUT_H     = 0x39;

// // Globale Variablen für Rohdaten
// int16_t accel_x, accel_y, accel_z;
// int16_t gyro_x, gyro_y, gyro_z;
// int16_t temperature;

// /**
//  * @brief Schreibt ein einzelnes Byte in ein Sensor-Register über SPI.
//  */
// void spi_write_register(uint8_t reg, uint8_t data) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(reg & 0x7F); // R/W-Bit = 0 für Schreiben
//   SPI.transfer(data);
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
// }

// /**
//  * @brief Liest mehrere Bytes von aufeinanderfolgenden Sensor-Registern über SPI.
//  */
// void spi_read_registers(uint8_t start_reg, uint8_t* buffer, uint8_t count) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(start_reg | 0x80); // R/W-Bit = 1 für Lesen
//   for (uint8_t i = 0; i < count; i++) {
//     buffer[i] = SPI.transfer(0x00); // Dummy-Byte senden, um zu empfangen
//   }
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
// }

// void setup() {
//   Serial.begin(115200);

//   // --- HANDSHAKE ---
//   // Warten, bis der Computer (Python) ein Zeichen sendet, BEVOR wir irgendetwas anderes tun.
//   while (Serial.available() == 0) {
//     delay(10);
//   }
//   // Eingehendes Zeichen aus dem Puffer lesen und verwerfen, um ihn zu leeren.
//   Serial.read();

//   // --- INITIALISIERUNG ---
//   pinMode(CS_PIN, OUTPUT);
//   digitalWrite(CS_PIN, HIGH);
//   SPI.begin();

//   // --- SENSOR-CHECK ---
//   uint8_t whoami;
//   spi_read_registers(REG_WHO_AM_I, &whoami, 1);
//   if (whoami != EXPECTED_ID) {
//     // Wenn der Sensor nicht gefunden wird, senden wir eine Fehlermeldung statt des Headers.
//     Serial.println("ERROR: Sensor not found!");
//     while (1); // Programm anhalten
//   }

//   // --- SENSOR AUFWECKEN ---
//   spi_write_register(REG_PWR_MGMT_1, 0x01);
//   delay(100); // Dem Sensor einen Moment Zeit geben, sich zu stabilisieren

//   // --- HEADER SENDEN ---
//   // Jetzt, da wir sicher sind, dass Python zuhört und der Sensor funktioniert, senden wir den Header.
//   Serial.println("Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_C");
// }

// void loop() {
//   uint8_t buffer[6]; // Puffer zum Empfangen der Daten

//   // Daten von allen Sensoren lesen
//   spi_read_registers(REG_ACCEL_XOUT_H, buffer, 6);
//   accel_x = (buffer[0] << 8) | buffer[1];
//   accel_y = (buffer[2] << 8) | buffer[3];
//   accel_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_GYRO_XOUT_H, buffer, 6);
//   gyro_x = (buffer[0] << 8) | buffer[1];
//   gyro_y = (buffer[2] << 8) | buffer[3];
//   gyro_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_TEMP_OUT_H, buffer, 2);
//   temperature = (buffer[0] << 8) | buffer[1];

//   // Daten als eine einzige, kommagetrennte Zeile ausgeben
//   Serial.print(accel_x);
//   Serial.print(",");
//   Serial.print(accel_y);
//   Serial.print(",");
//   Serial.print(accel_z);
//   Serial.print(",");
//   Serial.print(gyro_x);
//   Serial.print(",");
//   Serial.print(gyro_y);
//   Serial.print(",");
//   Serial.print(gyro_z);
//   Serial.print(",");
//   float temp_c = (temperature / 333.87) + 21.0;
//   Serial.println(temp_c);

//   delay(100); // 10 Messungen pro Sekunde
// }


// #include <SPI.h>

// // Pin-Definitionen für SPI
// constexpr uint8_t CS_PIN = 17;

// // Wichtige Register des ICM-20948 (User Bank 0)
// constexpr uint8_t REG_WHO_AM_I     = 0x00;
// constexpr uint8_t EXPECTED_ID      = 0xEA;
// constexpr uint8_t REG_USER_CTRL    = 0x03;
// constexpr uint8_t REG_PWR_MGMT_1   = 0x06;
// constexpr uint8_t REG_PWR_MGMT_2   = 0x07;
// constexpr uint8_t REG_INT_PIN_CFG  = 0x0F;
// constexpr uint8_t REG_ACCEL_CONFIG = 0x14;
// constexpr uint8_t REG_GYRO_CONFIG  = 0x15;
// constexpr uint8_t REG_ACCEL_XOUT_H = 0x2D;
// constexpr uint8_t REG_GYRO_XOUT_H  = 0x33;
// constexpr uint8_t REG_TEMP_OUT_H   = 0x39;

// // Globale Variablen für Rohdaten
// int16_t accel_x, accel_y, accel_z;
// int16_t gyro_x, gyro_y, gyro_z;
// int16_t temperature;

// // Timer für Register-Ausgabe
// unsigned long lastRegisterReadTime = 0;
// const unsigned long registerReadInterval = 4000; // 4 Sekunden

// /**
//  * @brief Schreibt ein einzelnes Byte in ein Sensor-Register über SPI.
//  */
// void spi_write_register(uint8_t reg, uint8_t data) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(reg & 0x7F);
//   SPI.transfer(data);
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
// }

// /**
//  * @brief Liest ein einzelnes Byte von einem Sensor-Register über SPI.
//  */
// uint8_t spi_read_register(uint8_t reg) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(reg | 0x80);
//   uint8_t value = SPI.transfer(0x00);
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
//   return value;
// }

// /**
//  * @brief Liest mehrere Bytes von aufeinanderfolgenden Sensor-Registern über SPI.
//  */
// void spi_read_registers(uint8_t start_reg, uint8_t* buffer, uint8_t count) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN, LOW);
//   SPI.transfer(start_reg | 0x80);
//   for (uint8_t i = 0; i < count; i++) {
//     buffer[i] = SPI.transfer(0x00);
//   }
//   digitalWrite(CS_PIN, HIGH);
//   SPI.endTransaction();
// }

// /**
//  * @brief Gibt den Status der wichtigsten Konfigurationsregister aus.
//  */
// void printRegisterStatus() {
//   Serial.println("\n## REGISTER STATUS ##");
//   Serial.print("  PWR_MGMT_1   (0x06): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_1), HEX);
//   Serial.print("  PWR_MGMT_2   (0x07): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_2), HEX);
//   Serial.print("  GYRO_CONFIG  (0x15): 0x"); Serial.println(spi_read_register(REG_GYRO_CONFIG), HEX);
//   Serial.print("  ACCEL_CONFIG (0x14): 0x"); Serial.println(spi_read_register(REG_ACCEL_CONFIG), HEX);
//   Serial.println("#####################\n");
// }

// void setup() {
//   Serial.begin(115200);

//   while (Serial.available() == 0) {
//     delay(10);
//   }
//   Serial.read();

//   pinMode(CS_PIN, OUTPUT);
//   digitalWrite(CS_PIN, HIGH);
//   SPI.begin();

//   uint8_t whoami = spi_read_register(REG_WHO_AM_I);
//   if (whoami != EXPECTED_ID) {
//     Serial.println("ERROR: Sensor not found!");
//     while (1);
//   }

//   spi_write_register(REG_PWR_MGMT_1, 0x01);
//   delay(100);

//   Serial.println("Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_C");
// }

// void loop() {
//   // Prüfen, ob es Zeit ist, die Register-Werte auszugeben
//   if (millis() - lastRegisterReadTime >= registerReadInterval) {
//     printRegisterStatus();
//     lastRegisterReadTime = millis(); // Timer zurücksetzen
//   }
  
//   uint8_t buffer[6];

//   // Daten von allen Sensoren lesen
//   spi_read_registers(REG_ACCEL_XOUT_H, buffer, 6);
//   accel_x = (buffer[0] << 8) | buffer[1];
//   accel_y = (buffer[2] << 8) | buffer[3];
//   accel_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_GYRO_XOUT_H, buffer, 6);
//   gyro_x = (buffer[0] << 8) | buffer[1];
//   gyro_y = (buffer[2] << 8) | buffer[3];
//   gyro_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_TEMP_OUT_H, buffer, 2);
//   temperature = (buffer[0] << 8) | buffer[1];

//   // CSV-Datenzeile ausgeben
//   Serial.print(accel_x);
//   Serial.print(",");
//   Serial.print(accel_y);
//   Serial.print(",");
//   Serial.print(accel_z);
//   Serial.print(",");
//   Serial.print(gyro_x);
//   Serial.print(",");
//   Serial.print(gyro_y);
//   Serial.print(",");
//   Serial.print(gyro_z);
//   Serial.print(",");
//   float temp_c = (temperature / 333.87) + 21.0;
//   Serial.println(temp_c);

//   delay(100);
// }


// #include <SPI.h>
// #include <Wire.h>
// #include <Adafruit_VL6180X.h>

// // --- Pin-Definitionen ---
// constexpr uint8_t CS_PIN_ICM = 17; // SPI Chip Select für ICM-20948
// constexpr uint8_t I2C_SDA_VL = 2;  // I2C SDA für VL6180X auf GP2
// constexpr uint8_t I2C_SCL_VL = 3;  // I2C SCL für VL6180X auf GP3

// // --- Sensor-Objekte ---
// Adafruit_VL6180X vl6180x = Adafruit_VL6180X();

// // --- Register des ICM-20948 (User Bank 0) ---
// constexpr uint8_t REG_WHO_AM_I     = 0x00;
// constexpr uint8_t EXPECTED_ID      = 0xEA;
// constexpr uint8_t REG_PWR_MGMT_1   = 0x06;
// constexpr uint8_t REG_PWR_MGMT_2   = 0x07;
// constexpr uint8_t REG_ACCEL_CONFIG = 0x14;
// constexpr uint8_t REG_GYRO_CONFIG  = 0x15;
// constexpr uint8_t REG_ACCEL_XOUT_H = 0x2D;
// constexpr uint8_t REG_GYRO_XOUT_H  = 0x33;
// constexpr uint8_t REG_TEMP_OUT_H   = 0x39;

// // Globale Variablen für Rohdaten
// int16_t accel_x, accel_y, accel_z;
// int16_t gyro_x, gyro_y, gyro_z;
// int16_t temperature;

// // Timer für Register-Ausgabe
// unsigned long lastRegisterReadTime = 0;
// const unsigned long registerReadInterval = 4000; // 4 Sekunden

// // --- SPI Hilfsfunktionen für ICM-20948 ---
// void spi_write_register(uint8_t reg, uint8_t data) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN_ICM, LOW);
//   SPI.transfer(reg & 0x7F);
//   SPI.transfer(data);
//   digitalWrite(CS_PIN_ICM, HIGH);
//   SPI.endTransaction();
// }

// uint8_t spi_read_register(uint8_t reg) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN_ICM, LOW);
//   SPI.transfer(reg | 0x80);
//   uint8_t value = SPI.transfer(0x00);
//   digitalWrite(CS_PIN_ICM, HIGH);
//   SPI.endTransaction();
//   return value;
// }

// void spi_read_registers(uint8_t start_reg, uint8_t* buffer, uint8_t count) {
//   SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
//   digitalWrite(CS_PIN_ICM, LOW);
//   SPI.transfer(start_reg | 0x80);
//   for (uint8_t i = 0; i < count; i++) {
//     buffer[i] = SPI.transfer(0x00);
//   }
//   digitalWrite(CS_PIN_ICM, HIGH);
//   SPI.endTransaction();
// }

// void printRegisterStatus() {
//   Serial.println("\n## ICM-20948 REGISTER STATUS ##");
//   Serial.print("  PWR_MGMT_1   (0x06): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_1), HEX);
//   Serial.print("  PWR_MGMT_2   (0x07): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_2), HEX);
//   Serial.print("  GYRO_CONFIG  (0x15): 0x"); Serial.println(spi_read_register(REG_GYRO_CONFIG), HEX);
//   Serial.print("  ACCEL_CONFIG (0x14): 0x"); Serial.println(spi_read_register(REG_ACCEL_CONFIG), HEX);
//   Serial.println("###############################\n");
// }

// void setup() {
//   Serial.begin(115200);

//   while (Serial.available() == 0) { delay(10); }
//   Serial.read();

//   // --- Initialisierung I2C für VL6180X ---
//   Wire1.setSDA(I2C_SDA_VL);
//   Wire1.setSCL(I2C_SCL_VL);
//   Wire1.begin();
//   if (!vl6180x.begin(&Wire1)) {
//     Serial.println("ERROR: VL6180X sensor not found!");
//     while (1);
//   }

//   // --- Initialisierung SPI für ICM-20948 ---
//   pinMode(CS_PIN_ICM, OUTPUT);
//   digitalWrite(CS_PIN_ICM, HIGH);
//   SPI.begin();
//   uint8_t whoami = spi_read_register(REG_WHO_AM_I);
//   if (whoami != EXPECTED_ID) {
//     Serial.println("ERROR: ICM-20948 sensor not found!");
//     while (1);
//   }
//   spi_write_register(REG_PWR_MGMT_1, 0x01);
//   delay(100);

//   // --- Sende CSV Header mit neuen Spalten ---
//   Serial.println("Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_C,Distance_mm,Lux");
// }

// void loop() {
//   if (millis() - lastRegisterReadTime >= registerReadInterval) {
//     printRegisterStatus();
//     lastRegisterReadTime = millis();
//   }
  
//   // --- Daten vom ICM-20948 lesen (SPI) ---
//   uint8_t buffer[6];
//   spi_read_registers(REG_ACCEL_XOUT_H, buffer, 6);
//   accel_x = (buffer[0] << 8) | buffer[1];
//   accel_y = (buffer[2] << 8) | buffer[3];
//   accel_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_GYRO_XOUT_H, buffer, 6);
//   gyro_x = (buffer[0] << 8) | buffer[1];
//   gyro_y = (buffer[2] << 8) | buffer[3];
//   gyro_z = (buffer[4] << 8) | buffer[5];

//   spi_read_registers(REG_TEMP_OUT_H, buffer, 2);
//   temperature = (buffer[0] << 8) | buffer[1];

//   // --- Daten vom VL6180X lesen (I2C) ---
//   uint8_t distance = vl6180x.readRange();
//   float lux = vl6180x.readLux(VL6180X_ALS_GAIN_1);

//   // --- CSV-Datenzeile ausgeben ---
//   Serial.print(accel_x); Serial.print(",");
//   Serial.print(accel_y); Serial.print(",");
//   Serial.print(accel_z); Serial.print(",");
//   Serial.print(gyro_x); Serial.print(",");
//   Serial.print(gyro_y); Serial.print(",");
//   Serial.print(gyro_z); Serial.print(",");
//   float temp_c = (temperature / 333.87) + 21.0;
//   Serial.print(temp_c); Serial.print(",");
//   Serial.print(distance); Serial.print(",");
//   Serial.println(lux);

//   delay(100);
// }


#include <SPI.h>
#include <Wire.h>
#include <Adafruit_VL6180X.h>

// --- Pin-Definitionen ---
constexpr uint8_t CS_PIN_ICM = 17; // SPI Chip Select für ICM-20948
constexpr uint8_t I2C_SDA_VL = 2;  // I2C SDA für VL6180X auf GP2
constexpr uint8_t I2C_SCL_VL = 3;  // I2C SCL für VL6180X auf GP3

// --- Sensor-Objekte ---
Adafruit_VL6180X vl6180x = Adafruit_VL6180X();

// --- Register des ICM-20948 (User Bank 0) ---
constexpr uint8_t REG_WHO_AM_I     = 0x00;
constexpr uint8_t EXPECTED_ID      = 0xEA;
constexpr uint8_t REG_PWR_MGMT_1   = 0x06;
constexpr uint8_t REG_PWR_MGMT_2   = 0x07;
constexpr uint8_t REG_ACCEL_CONFIG = 0x14;
constexpr uint8_t REG_GYRO_CONFIG  = 0x15;
constexpr uint8_t REG_ACCEL_XOUT_H = 0x2D;
constexpr uint8_t REG_GYRO_XOUT_H  = 0x33;
constexpr uint8_t REG_TEMP_OUT_H   = 0x39;

// Globale Variablen für Rohdaten
int16_t accel_x, accel_y, accel_z;
int16_t gyro_x, gyro_y, gyro_z;
int16_t temperature;

// Timer für Register-Ausgabe
unsigned long lastRegisterReadTime = 0;
const unsigned long registerReadInterval = 4000; // 4 Sekunden

// --- SPI Hilfsfunktionen für ICM-20948 ---
void spi_write_register(uint8_t reg, uint8_t data) {
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_PIN_ICM, LOW);
  SPI.transfer(reg & 0x7F);
  SPI.transfer(data);
  digitalWrite(CS_PIN_ICM, HIGH);
  SPI.endTransaction();
}

uint8_t spi_read_register(uint8_t reg) {
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_PIN_ICM, LOW);
  SPI.transfer(reg | 0x80);
  uint8_t value = SPI.transfer(0x00);
  digitalWrite(CS_PIN_ICM, HIGH);
  SPI.endTransaction();
  return value;
}

void spi_read_registers(uint8_t start_reg, uint8_t* buffer, uint8_t count) {
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_PIN_ICM, LOW);
  SPI.transfer(start_reg | 0x80);
  for (uint8_t i = 0; i < count; i++) {
    buffer[i] = SPI.transfer(0x00);
  }
  digitalWrite(CS_PIN_ICM, HIGH);
  SPI.endTransaction();
}

void printRegisterStatus() {
  Serial.println("\n## ICM-20948 REGISTER STATUS ##");
  Serial.print("  PWR_MGMT_1   (0x06): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_1), HEX);
  Serial.print("  PWR_MGMT_2   (0x07): 0x"); Serial.println(spi_read_register(REG_PWR_MGMT_2), HEX);
  Serial.print("  GYRO_CONFIG  (0x15): 0x"); Serial.println(spi_read_register(REG_GYRO_CONFIG), HEX);
  Serial.print("  ACCEL_CONFIG (0x14): 0x"); Serial.println(spi_read_register(REG_ACCEL_CONFIG), HEX);
  Serial.println("###############################\n");
}

void setup() {
  Serial.begin(115200);

  while (Serial.available() == 0) { delay(10); }
  Serial.read();

  // --- Initialisierung I2C für VL6180X ---
  Wire1.setSDA(I2C_SDA_VL);
  Wire1.setSCL(I2C_SCL_VL);
  Wire1.begin();
  if (!vl6180x.begin(&Wire1)) {
    Serial.println("ERROR: VL6180X sensor not found!");
    while (1);
  }
  Serial.println("STATUS: VL6180X sensor found and initialized.");

  // --- Initialisierung SPI für ICM-20948 ---
  pinMode(CS_PIN_ICM, OUTPUT);
  digitalWrite(CS_PIN_ICM, HIGH);
  SPI.begin();
  uint8_t whoami = spi_read_register(REG_WHO_AM_I);
  if (whoami != EXPECTED_ID) {
    Serial.println("ERROR: ICM-20948 sensor not found!");
    while (1);
  }
  Serial.println("STATUS: ICM-20948 sensor found and initialized.");
  spi_write_register(REG_PWR_MGMT_1, 0x01);
  delay(100);

  // --- Sende CSV Header mit neuen Spalten ---
  Serial.println("Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_C,Distance_mm,Lux");
}

void loop() {
  if (millis() - lastRegisterReadTime >= registerReadInterval) {
    printRegisterStatus();
    lastRegisterReadTime = millis();
  }
  
  // --- Daten vom ICM-20948 lesen (SPI) ---
  uint8_t buffer[6];
  spi_read_registers(REG_ACCEL_XOUT_H, buffer, 6);
  accel_x = (buffer[0] << 8) | buffer[1];
  accel_y = (buffer[2] << 8) | buffer[3];
  accel_z = (buffer[4] << 8) | buffer[5];

  spi_read_registers(REG_GYRO_XOUT_H, buffer, 6);
  gyro_x = (buffer[0] << 8) | buffer[1];
  gyro_y = (buffer[2] << 8) | buffer[3];
  gyro_z = (buffer[4] << 8) | buffer[5];

  spi_read_registers(REG_TEMP_OUT_H, buffer, 2);
  temperature = (buffer[0] << 8) | buffer[1];

  // --- Daten vom VL6180X lesen (I2C) ---
  uint8_t distance = vl6180x.readRange();
  // *** HIER IST DIE ÄNDERUNG: Empfindlichkeit wurde erhöht ***
  float lux = vl6180x.readLux(VL6180X_ALS_GAIN_40); // War vorher VL6180X_ALS_GAIN_1

  // --- CSV-Datenzeile ausgeben ---
  Serial.print(accel_x); Serial.print(",");
  Serial.print(accel_y); Serial.print(",");
  Serial.print(accel_z); Serial.print(",");
  Serial.print(gyro_x); Serial.print(",");
  Serial.print(gyro_y); Serial.print(",");
  Serial.print(gyro_z); Serial.print(",");
  float temp_c = (temperature / 333.87) + 21.0;
  Serial.print(temp_c); Serial.print(",");
  Serial.print(distance); Serial.print(",");
  Serial.println(lux);

  delay(100);
}

