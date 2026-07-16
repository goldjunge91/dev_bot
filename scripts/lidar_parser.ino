#include <SoftwareSerial.h>
#include <string.h>

// --- Lidar Paket Struktur ---
// Ein Paket hat 22 Bytes:
// <0xFA> <ANGLE_INDEX> <SPEED_LSB> <SPEED_MSB> <4x DATA (jeweils 4 Bytes)> <CHECKSUM_LSB> <CHECKSUM_MSB>
// Jedes Datenpaket enthält 4 Messungen. Eine Messung besteht aus:
// <DIST_LSB> <DIST_MSB> <QUAL_LSB> <QUAL_MSB>

#define PACKET_SIZE 22
#define DATA_SIZE 7 // Format für Python: [Winkel, RPM, Distanz 1, Distanz 2, Distanz 3, Distanz 4, ChecksumStatus]

// --- PIN BELEGUNG (Vom Nutzer definiert) ---
#define RX_PIN 10         // Lidar TX -> Arduino Pin 10 (SoftwareSerial RX)
#define MOTOR_IN1_PIN 5   // DRV8833 IN1 (PWM Pin zur Geschwindigkeitsregelung)
#define MOTOR_IN2_PIN 4   // DRV8833 IN2 (Fest auf LOW)
#define DRV_EEP_PIN 7     // DRV8833 EEP / Sleep Pin (Muss HIGH sein zum Aktivieren)

// --- PARAMETER ---
#define BAUDRATE_SENSOR 115200
#define BAUDRATE_PC 115200
#define MIN_POWER 0
#define MAX_POWER 255
#define TARGET_RPM 300    // Ziel-Drehzahl: 300 RPM (5 Hz)

// --- GLOBALE VARIABLEN ---
SoftwareSerial lidarSensor(RX_PIN, 11); // RX an 10, TX an 11 (nicht belegt)
uint8_t packet[PACKET_SIZE];
unsigned int packetIndex = 0;
bool waitPacket = true;
int outData[DATA_SIZE]; // Winkel, RPM, D1, D2, D3, D4, Checksum_Valid

// --- PID REGELUNG VARIABLEN ---
double proportionalTerm = 0;
double derivativeTerm   = 0; 
double integralTerm     = 0;
double previousSpeed    = 0;
int currentSpeed        = 0; // Gemessene RPM

// PID Koeffizienten (können bei Bedarf im Betrieb angepasst werden)
double kp = 2.5;
double ki = 0.4; 
double kd = 0.2;

void setup() {
    // Timer 1 Setup (Trigger für PID-Regelkreis ca. alle 0.262 Sekunden bei Overflow)
    noInterrupts();     
    TCCR1A = 0;
    TCCR1B = 0;
    TCCR1B |= (1 << CS11) | (1 << CS10); // Prescaler 64  
    TIMSK1 |= (1 << TOIE1);              // Overflow Interrupt aktivieren
    interrupts();
    
    // Serielle Schnittstellen starten
    lidarSensor.begin(BAUDRATE_SENSOR);
    Serial.begin(BAUDRATE_PC);

    // Pins konfigurieren
    pinMode(RX_PIN, INPUT);
    pinMode(DRV_EEP_PIN, OUTPUT);
    pinMode(MOTOR_IN1_PIN, OUTPUT);
    pinMode(MOTOR_IN2_PIN, OUTPUT);

    // DRV8833 aufwecken
    digitalWrite(DRV_EEP_PIN, HIGH);
    digitalWrite(MOTOR_IN2_PIN, LOW); // Vorwärtslauf aktivieren

    // Sanfter Anlauf (Kickstart) des Lidar-Motors
    analogWrite(MOTOR_IN1_PIN, MAX_POWER);
    delay(1000);
    analogWrite(MOTOR_IN1_PIN, 130); // Initialer PWM-Schätzwert
    
    // Paket-Buffer initialisieren
    memset(packet, 0, PACKET_SIZE);
}

void loop() {
    // Liest serielle Bytes vom Lidar-Sensor
    if (lidarSensor.available() > 0) {
        uint8_t receivedByte = lidarSensor.read();

        if (waitPacket) {
            if (receivedByte == 0xFA) { // Start-Byte gefunden
                packetIndex = 0;
                waitPacket = false;
                packet[packetIndex++] = receivedByte;
            }
        } else {
            packet[packetIndex++] = receivedByte;
            
            if (packetIndex >= PACKET_SIZE) {
                waitPacket = true; // Nächstes Paket erwarten
                decodePacket(packet);
            }
        }
    }
}

// Timer1 ISR: Führt die PID-Motorregelung alle ~262 ms aus
ISR(TIMER1_OVF_vect) {
    motorSpeedPID(TARGET_RPM, currentSpeed, 0.262);
}

// Lidar-Datenpaket decodieren
void decodePacket(uint8_t pkt[]) {
    // 1. Checksumme validieren
    uint16_t expectedChecksum = pkt[20] | (pkt[21] << 8);
    bool isChecksumOk = validateChecksum(pkt, expectedChecksum, 20);

    // 2. Winkel berechnen
    // Index (pkt[1]) reicht von 0xA0 (160) bis 0xF9 (249)
    int angleIndex = pkt[1] - 0xA0;
    int startAngle = angleIndex * 4; // Startwinkel dieses Pakets
    
    if (startAngle < 0 || startAngle >= 360) return;

    // 3. Geschwindigkeit (RPM) extrahieren
    uint16_t speedRaw = pkt[2] | (pkt[3] << 8);
    int calculatedRPM = speedRaw / 64; // RPM-Konvertierung

    // Glättungsfilter für RPM-Ausreißer
    if (abs(calculatedRPM - currentSpeed) > 100) {
        currentSpeed = currentSpeed * 0.9 + calculatedRPM * 0.1;
    } else {
        currentSpeed = calculatedRPM;
    }

    // 4. Distanzwerte extrahieren
    outData[0] = startAngle;
    outData[1] = currentSpeed;

    for (int i = 0; i < 4; i++) {
        int offset = 4 + (i * 4);
        uint8_t distL = pkt[offset];
        uint8_t distH = pkt[offset + 1];

        // Statusflag: Ungültige Messung, falls das MSB von distH gesetzt ist
        bool invalid = (distH & 0x80); 
        
        uint16_t distance = distL | ((distH & 0x3F) << 8);

        if (invalid || distance == 0) {
            outData[2 + i] = 0; // Ungültige Messungen mit 0 markieren
        } else {
            outData[2 + i] = distance; // Distanz in mm
        }
    }

    outData[6] = isChecksumOk ? 1 : 0; // Checksummenstatus mitsenden

    // Datenpaket über USB an den PC senden (durch Tabs getrennt)
    sendSerialData(outData, DATA_SIZE);
}

// Sendet die geparsten Lidar-Daten an das Python-Skript
void sendSerialData(int dataArray[], int size) {
    for (int i = 0; i < size; i++) {
        Serial.print(dataArray[i]);
        if (i < size - 1) {
            Serial.print('\t');
        }
    }
    Serial.println();
}

// PID-Geschwindigkeitsregler für den Motor
void motorSpeedPID(int targetSpeed, int currentSpeed, double deltaT) {
    proportionalTerm = targetSpeed - currentSpeed;
    derivativeTerm = (currentSpeed - previousSpeed) / deltaT;
    integralTerm += proportionalTerm * deltaT;

    int controlEffort = (kp * proportionalTerm + kd * derivativeTerm + ki * integralTerm) + currentSpeed;

    // Anti-Windup (Begrenzung des Integrators bei Sättigung)
    if (controlEffort > MAX_POWER) {
        integralTerm -= proportionalTerm * deltaT;
        controlEffort = MAX_POWER;
    } else if (controlEffort < MIN_POWER) {
        integralTerm -= proportionalTerm * deltaT;
        controlEffort = MIN_POWER;
    }

    previousSpeed = currentSpeed;
    
    // PWM Signal an DRV8833 senden
    analogWrite(MOTOR_IN1_PIN, controlEffort);
}

// Berechnet die Checksumme für das Paket
bool validateChecksum(uint8_t pkt[], uint16_t targetSum, uint8_t size) {
    uint32_t chk32 = 0;
    for (int i = 0; i < size / 2; i++) {
        uint16_t val = pkt[i * 2] | (pkt[i * 2 + 1] << 8);
        chk32 = (chk32 << 1) + val;
    }
    uint32_t checksum = (chk32 & 0x7FFF) + (chk32 >> 15);
    return (uint16_t)(checksum & 0x7FFF) == targetSum;
}
