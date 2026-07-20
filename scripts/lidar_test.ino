#include <SoftwareSerial.h>

// Pins für den DRV8833 Motortreiber
const int MOTOR_PWM_PIN = 5;  // IN1 an DRV8833
// IN2 an DRV8833 sollte fest mit GND verbunden sein!

// SoftwareSerial Pins für das Lidar
// Arduino RX (Pin 2) -> Lidar TX
// Arduino TX (Pin 3) -> Lidar RX (optional)
SoftwareSerial lidarSerial(2, 3);

void setup() {
    // Starte Verbindung zum PC (Serieller Monitor)
    Serial.begin(115200);
    while (!Serial) {
        ;  // Warten auf USB-Verbindung
    }
    Serial.println("--- LDS-1S Lidar Verbindungstest gestartet ---");

    // Konfiguriere Motor-Steuerpin
    pinMode(MOTOR_PWM_PIN, OUTPUT);

    // Motor starten: LDS-1S benötigt ca. 5 Hz (300 RPM).
    // Ein PWM-Wert von ca. 120-180 (von 255) reicht meistens aus, um den Motor drehen zu lassen.
    // Falls der Lidar sich nicht dreht, erhöhe den Wert leicht (z.B. auf 200).
    analogWrite(MOTOR_PWM_PIN, 150);
    Serial.println("Lidar Motor gestartet (PWM: 150)...");

    // Starte Verbindung zum Lidar (LDS-1S läuft typischerweise mit 115200 Baud)
    lidarSerial.begin(115200);
    Serial.println("Warte auf Lidar-Daten...");
}

void loop() {
    // Leite alle ankommenden Bytes vom Lidar direkt an den PC weiter
    if (lidarSerial.available()) {
        byte data = lidarSerial.read();

        // Wir geben die Daten als Hexadezimal-Werte aus, da Lidar-Daten Binärprotokolle sind
        if (data < 0x10) Serial.print("0");
        Serial.print(data, HEX);
        Serial.print(" ");

        // Zeilenumbruch zur besseren Lesbarkeit alle 20 Bytes (ein Paket hat oft 22 oder 42 Bytes)
        static int byteCount = 0;
        byteCount++;
        if (byteCount >= 22) {
            Serial.println();
            byteCount = 0;
        }
    }
}
