//
// Created by tozzi on 18.02.2026.
//

#ifndef FIRINGFSM_H
#define FIRINGFSM_H

#include "../../include/Config.h"

#include <Arduino.h>

/**
 * @brief Zustände der Schusssequenz (Finite State Machine).
 */
enum class FiringState {
    IDLE,         ///< System bereit, Motoren aus
    ARMING,       ///< Sicherheitsverzögerung vor der Aktivierung
    ARMED,        ///< System aktiv, bereit zum Schießen
    DISARMING,    ///< Sicherheitsverzögerung/Aktion vor Inaktivität
    DISARMED,     ///< Sicherer Zustand, Befehle werden ignoriert
    SPINNING_UP,  ///< Schwungräder (Flywheels) beschleunigen
    PUSHING,      ///< Pusher-Servo fährt aus, um den Dart zuzuführen
    BRAKING,      ///< Pusher-Servo fährt zurück/bremst
    COOLDOWN,     ///< Kurze Pause nach dem Schuss
    ESC_TEST,     ///< Manueller Test der Flywheel-Geschwindigkeit
    CALIBRATING   ///< ESC-Kalibrierungsmodus
};

// Callback-Typen (Funktionszeiger)
// Diese Typen definieren die "Form" der Funktionen, die die FSM aufrufen kann,
// ohne die genauen Hardware-Details zu kennen (Trennung von Logik und Hardware).

/** @brief Callback ohne Parameter (z.B. für einfache Aktionen wie Attach/Detach). */
typedef void (*SimpleCallback)();

/** @brief Callback zur Steuerung der Motorleistung (Eingabe: 0 bis 100%). */
typedef void (*EscCallback)(int powerPercent);

/** @brief Callback zur Steuerung eines Servos über ein PWM-Signal (Eingabe: Mikrosekunden). */
typedef void (*ServoCallback)(int microseconds);

/** @brief Callback zur Ausgabe von System-/Debug-Textnachrichten. */
typedef void (*DebugCallback)(const char *msg);

/**
 * @brief Zustandsautomat (FSM) für den Nerf-Launcher.
 *
 * Verwaltet das komplexe Timing und die Zustandsübergänge für ein sicheres
 * Abfeuern von Darts. Entkoppelt die reine Logik von der Arduino-Hardware-Implementierung
 * (Servos/Pins) über Callback-Funktionen.
 */
class FiringFSM {
private:
    FiringState _currentState;
    FiringState _nextState;

    uint32_t _stateStartTime;  // uint32_t: Vorzeichenlose 32-Bit-Ganzzahl (Standard in Arduino)
    uint32_t _lastActivityTime;

    // Transition-Parameter
    int _targetPower;
    int _shotDuration;
    int _shotNeutral;
    bool _isArmed;

    // Hardware-Callbacks
    EscCallback _onFlywheelPower;
    ServoCallback _onShotServo;
    SimpleCallback _onAttachESCs;
    SimpleCallback _onDetachESCs;
    SimpleCallback _onAttachShot;
    SimpleCallback _onDetachShot;
    DebugCallback _onDebug;

public:
    /**
     * @brief Konstruktor
     *
     * @param onFlywheelPower Callback zum Setzen der ESC-Leistung (0-100).
     * @param onShotServo Callback zum Setzen der Pusher-Servo-Position (µs).
     * @param onAttachESCs Callback zum Anhängen (attach) der ESC-Pins.
     * @param onDetachESCs Callback zum Lösen (detach) der ESC-Pins.
     * @param onAttachShot Callback zum Anhängen des Pusher-Servos.
     * @param onDetachShot Callback zum Lösen des Pusher-Servos.
     * @param onDebug Callback für Debug-Textausgaben.
     */
    FiringFSM(EscCallback onFlywheelPower,
              ServoCallback onShotServo,
              SimpleCallback onAttachESCs,
              SimpleCallback onDetachESCs,
              SimpleCallback onAttachShot,
              SimpleCallback onDetachShot,
              DebugCallback onDebug);

    /**
     * @brief Wertet zeit- oder logikbasierte Zustandsübergänge aus.
     * Setzt nur _nextState, führt aber keine direkten Hardware-Aktionen aus.
     */
    void evalTransition();

    /**
     * @brief Übernimmt _nextState und führt Hardware-Aktionen aus.
     * Wird nur aktiv, wenn sich der Zustand ändert (_nextState != _currentState)
     * und feuert die Ein- und Austrittsaktionen genau einmalig ab.
     * Muss in der Hauptschleife nach `evalTransition()` aufgerufen werden.
     */
    void evalState();

    // Events & Trigger
    void triggerArming();

    void triggerDisarming();

    void triggerFire(int power);

    void triggerCalibration();

    void triggerEscTest(int power);

    void recordActivity();

    // Setter
    void setShotDuration(int ms);

    void setShotNeutral(int us);

    // Getter
    FiringState getCurrentState() const;

    bool isArmed() const;

    bool canFire() const;

    int getShotDuration() const;

    int getShotNeutral() const;
};

#endif  // FIRINGFSM_H
