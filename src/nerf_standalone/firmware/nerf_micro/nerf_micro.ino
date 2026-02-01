/*
 * Nerf Launcher Firmware for Arduino Pro Micro (Brushless ESC Version)
 * 
 * Hardware Mapping:
 * - Tilt Servo: Pin 9 (Standard Servo)
 * - Pusher Servo: Pin 10 (Continuous Servo or Standard)
 * - Flywheel Left: Pin 5 (ESC - Servo Signal)
 * - Flywheel Right: Pin 6 (ESC - Servo Signal)
 * 
 * Serial Protocol (115200 baud):
 * - t <angle>: Set Tilt Servo (0-180)
 * - p <speed>: Set Pusher Speed/Angle (0-180)
 * - f <val_l> <val_r>: Set Flywheel Speed (0-255 mapped to 1000-2000us)
 * - a: ARM System (Sends Min throttle to ESCs)
 * - d: DISARM System (Stops motors)
 */

#include <Servo.h>

// --- Configuration ---
const int PIN_FLYWHEEL_L = 5;
const int PIN_FLYWHEEL_R = 6;
const int PIN_SERVO_TILT = 9;
const int PIN_SERVO_PUSHER = 10;

const long BAUD_RATE = 115200;

// ESC Limits
const int ESC_MIN_US = 1000;
const int ESC_MAX_US = 2000;
const int ESC_ARM_US = 1000;

class Launcher {
private:
    Servo tiltServo;
    Servo pusherServo;
    Servo escLeft;
    Servo escRight;
    
    bool isArmed = false;

public:
    void begin() {
        // Init Servos & ESCs
        tiltServo.attach(PIN_SERVO_TILT);
        pusherServo.attach(PIN_SERVO_PUSHER);
        escLeft.attach(PIN_FLYWHEEL_L);
        escRight.attach(PIN_FLYWHEEL_R);

        // Safe Start (Disarmed)
        disarm();
        
        // Center Servos
        setTilt(90);
        setPusher(90); 
    }

    void arm() {
        isArmed = true;
        // ESCs usually need min signal to arm
        escLeft.writeMicroseconds(ESC_ARM_US);
        escRight.writeMicroseconds(ESC_ARM_US);
    }

    void disarm() {
        isArmed = false;
        escLeft.writeMicroseconds(ESC_ARM_US);
        escRight.writeMicroseconds(ESC_ARM_US);
        pusherServo.write(90); // Stop pusher
    }

    void setTilt(int angle) {
        angle = constrain(angle, 0, 180);
        tiltServo.write(angle);
    }

    void setPusher(int val) {
        if (!isArmed) val = 90; // Safety
        val = constrain(val, 0, 180);
        pusherServo.write(val);
    }

    void setFlywheels(int val_l, int val_r) {
        if (!isArmed) {
            val_l = 0;
            val_r = 0;
        }
        
        // Map 0-255 -> 1000-2000us
        int us_l = map(constrain(val_l, 0, 255), 0, 255, ESC_MIN_US, ESC_MAX_US);
        int us_r = map(constrain(val_r, 0, 255), 0, 255, ESC_MIN_US, ESC_MAX_US);
        
        escLeft.writeMicroseconds(us_l);
        escRight.writeMicroseconds(us_r);
    }

    bool getArmed() { return isArmed; }
};

class SerialComms {
private:
    Launcher& launcher;
    String inputBuffer;

public:
    SerialComms(Launcher& l) : launcher(l) {
        inputBuffer.reserve(32);
    }

    void update() {
        while (Serial.available()) {
            char c = Serial.read();
            if (c == '\n' || c == '\r') {
                if (inputBuffer.length() > 0) {
                    processCommand(inputBuffer);
                    inputBuffer = "";
                }
            } else {
                inputBuffer += c;
            }
        }
    }

    void processCommand(String cmd) {
        char type = cmd.charAt(0);
        String args = cmd.substring(2); // Skip command char and space
        
        if (type == 'a') {
            launcher.arm();
            Serial.println("OK: ARMED");
        }
        else if (type == 'd') {
            launcher.disarm();
            Serial.println("OK: DISARMED");
        }
        else if (type == 't') {
            int angle = args.toInt();
            launcher.setTilt(angle);
            Serial.println("OK: Tilt");
        } 
        else if (type == 'p') {
            int val = args.toInt();
            launcher.setPusher(val);
            Serial.println("OK: Pusher");
        } 
        else if (type == 'f') {
            int spaceIdx = args.indexOf(' ');
            if (spaceIdx != -1) {
                int val_l = args.substring(0, spaceIdx).toInt();
                int val_r = args.substring(spaceIdx + 1).toInt();
                launcher.setFlywheels(val_l, val_r);
                Serial.println("OK: Flywheels");
            }
        }
    }
};

// --- Main Program ---

Launcher nerfLauncher;
SerialComms comms(nerfLauncher);

void setup() {
    Serial.begin(BAUD_RATE);
    nerfLauncher.begin();
    
    pinMode(LED_BUILTIN, OUTPUT);
    // Blink 3 times to signal ready
    for(int i=0; i<3; i++) {
        digitalWrite(LED_BUILTIN, HIGH); delay(100);
        digitalWrite(LED_BUILTIN, LOW); delay(100);
    }
}

void loop() {
    comms.update();
}
