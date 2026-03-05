//
// Created by tozzi on 18.02.2026.
//

#ifndef LAUNCHER_H
#define LAUNCHER_H

#include "../../include/Config.h"
#include "../Utils/SerialOutput.h"
#include "FiringFSM.h"

#include <Arduino.h>  // Basis-Header der Arduino-Bibliothek
#include <Servo.h>    // Arduino-Bibliothek zur Ansteuerung von Servomotoren

/**
 * @brief Zentrale Hardware-Schnittstelle für den Nerf-Launcher.
 *
 * Bündelt die Logik der FiringFSM sowie die Hardware (ESCs und Pusher-Servo)
 * und bietet aufgeräumte Methoden zur Steuerung. Schlägt die Brücke zwischen
 * abstrakter Zustandsmaschine und physischen Arduino-Funktionen.
 */
class Launcher {
private:
    Servo _escLeft, _escRight, _shot;
    FiringFSM _fsm;

    // Static pointer for callbacks
    static Launcher *_instance;

    enum class ManualState {
        IDLE,
        TEST_SHOT_PUSH,
        TEST_SHOT_BRAKE,
        TEST_SHOT_CENTER,
        DANGEROUS_SHOT_PUSH,
        DANGEROUS_SHOT_BRAKE,
        DANGEROUS_SHOT_CENTER,
        NUDGE_OUT,
        NUDGE_CENTER
    };
    ManualState _manualState;
    uint32_t _manualTimer;

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
     * @brief Initialisiert die Hardware in einem sicheren (SAFE) Zustand.
     * Löst alle Servos (detach), um unkontrollierte Bewegungen beim Start zu verhindern.
     */
    void begin();

    /**
     * @brief Hauptschleifen-Update.
     * Treibt die FSM (Übergangs- und Aktionslogik) sowie manuelle nicht-blockierende Aktionen an.
     */
    void update();

    // Manual Hardware Actions (not FSM-controlled)

    /**
     * @brief Löst einen Testschuss ohne Einmischung der FSM aus (nur zu Debug-Zwecken).
     * @param ms Dauer des Pusher-Ausfahrens in Millisekunden.
     */
    void testShot(int ms);

    /**
     * @brief Löst einen Schuss mit laufenden Flywheels aus. Im Gegensatz zu testShot greift
     * diese Funktion nicht in den Zustand der ESCs ein.
     * @param ms Dauer des Pusher-Ausfahrens in Millisekunden.
     */
    void dangerousShot(int ms);

    /**
     * @brief Bewegt den Pusher-Servo minimal, um Ladehemmungen zu lösen oder zur Justierung.
     * @param forward Richtung des Stupsens (wahr = vorwärts).
     */
    void nudge(bool forward);

    /**
     * @brief Sendet rohe PWM-Signale an die ESCs (Achtung: Gefährlich!).
     * Dies funktioniert aus Sicherheitsgründen nur im Zustand ARMED.
     * @param us Pulsbreite in Mikrosekunden.
     */
    void setRawPWM(int us);

    // Config with Debug Output
    void setZS(int v);

    void setD(int v);

    // Getters
    int getShotZero() {
        return _fsm.getShotNeutral();
    }
    int getShotDur() {
        return _fsm.getShotDuration();
    }

    // FSM Access
    FiringFSM &getFSM() {
        return _fsm;
    }

    // ESC Access for Debug
    Servo &getLeftESC() {
        return _escLeft;
    }
    Servo &getRightESC() {
        return _escRight;
    }
};

#endif  // LAUNCHER_H