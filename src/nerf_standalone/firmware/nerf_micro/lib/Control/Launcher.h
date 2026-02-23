//
// Created by tozzi on 18.02.2026.
//

#ifndef LAUNCHER_H
#define LAUNCHER_H

#include "../../include/Config.h"
#include "../Utils/SerialOutput.h"
#include "FiringFSM.h"
#include <Arduino.h>
#include <Servo.h>

/**
 * @brief Main Hardware Interface for the Nerf Launcher.
 *
 * Aggregates the FiringFSM, Servos (ESCs and Pusher), and provides
 * high-level methods to control the launcher. Bridges the gap between
 * abstract FSM logic and concrete Arduino/Servo calls.
 */
class Launcher {
private:
    Servo _escLeft, _escRight, _shot;
    FiringFSM _fsm;

    // Static pointer for callbacks
    static Launcher *_instance;

    // Interne Hardware-Methoden (genutzt von FSM)
    void setESCPower(int powerPercent);

    void setShotServo(int us);

    void attachESCs();

    void detachESCs();

    void attachShotServo();

    void detachShotServo();

    // Static Callbacks wrappers
    static void callbackESCPower(int pwr);

    static void callbackShotServo(int us);

    static void callbackAttachESCs();

    static void callbackDetachESCs();

    static void callbackAttachShot();

    static void callbackDetachShot();

    static void callbackDebug(const char *msg);

public:
    Launcher();

    /**
     * @brief Initializes hardware (SAFE state).
     * Detaches all servos to prevent startup movement.
     */
    void begin();

    /**
     * @brief Main loop update.
     * Drives the FSM (Entry/Transition/Exit logic).
     */
    void update();

    // Manual Hardware Actions (not FSM-controlled)

    /**
     * @brief Fires a shot without FSM (Debug/Test only).
     * @param ms Duration of the pusher extension in ms.
     */
    void testShot(int ms);

    /**
     * @brief Jiggles the pusher servo to unjam or test.
     * @param forward Direction to nudge.
     */
    void nudge(bool forward);

    /**
     * @brief Sets raw PWM for ESCs (Dangerous!).
     * Only works if system is ARMED.
     * @param us Pulse width in microseconds.
     */
    void setRawPWM(int us);

    // Config with Debug Output
    void setZS(int v);

    void setD(int v);

    // Getters
    int getShotZero() { return _fsm.getShotNeutral(); }
    int getShotDur() { return _fsm.getShotDuration(); }

    // FSM Access
    FiringFSM &getFSM() { return _fsm; }

    // ESC Access for Debug
    Servo &getLeftESC() { return _escLeft; }
    Servo &getRightESC() { return _escRight; }
};

#endif // LAUNCHER_H