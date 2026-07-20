//
// Created by tozzi on 18.02.2026.
//

#ifndef TILT_H
#define TILT_H

#include "../../include/Config.h"
// #include "../Utils/SerialOutput.h"
#include "SerialOutput.h"

#include <Arduino.h>  // Basis-Header der Arduino-Bibliothek
#include <Servo.h>    // Arduino-Bibliothek zur Ansteuerung von Servomotoren

/**
 * @brief Steuert den Neigungs-Servo (Pitch) für den Launcher.
 *
 * Behandelt das Bewegen des Tilt-Servos in Aufwärts-/Abwärts-Richtungen,
 * das minimale Stupsen (Nudge) und das Setzen spezifischer Winkel.
 * Nutzt nicht-blockierende Logik, um den Servo nach der Bewegung
 * abzuschalten (detach), um Strom zu sparen und Servozittern (Jitter) zu vermeiden.
 */
class TiltController {
private:
    Servo _tiltServo;  // Servo-Klasse aus der Arduino-Bibliothek
    //    bool _isMoving;
    //    uint32_t _endTime;
    enum class State { IDLE, MOVING, CENTERING, NUDGING_OUT, NUDGING_IN, HOLDING };
    State _state;
    uint32_t _stateEndTime;
    bool _nudgeUp;
    uint8_t _pin;
    int _neutralUs;

public:
    /**
     * @brief Konstruktor
     * @param pin Der GPIO-Pin für den Servo.
     * @param neutral Die neutrale (Mittel-) Pulsbreite in Mikrosekunden.
     */
    TiltController(uint8_t pin, int neutral);

    /**
     * @brief Wird in der Hauptschleife aufgerufen, um zeitgesteuerte Detachs zu handhaben.
     */
    void update();

    /**
     * @brief Bewegt den Neigungsmechanismus nach oben oder unten.
     *
     * @param up Wahr (True) für AUFWÄRTS, Falsch (False) für ABWÄRTS.
     * @param ms Dauer der Stromzufuhr (bestimmt die bewältigte Distanz).
     */
    void move(bool up, uint32_t ms);

    /**
     * @brief Kleine inkrementelle Bewegung (Nudge) zum Debuggen/Tuning.
     * @param up Richtung (wahr = nach oben).
     */
    void nudge(bool up);

    /**
     * @brief Setzt den internen "Neutral"-Referenzwert.
     * @param v Pulsbreite in Mikrosekunden.
     */
    void setNeutral(int v);

    /**
     * @brief Bewegt den Servo auf eine spezifische absolute Position.
     * @param us Pulsbreite in Mikrosekunden (ca. 1000-2000).
     */
    void setPosition(int us);

    int getNeutral();

    /**
     * @brief Zugriff auf den internen Servo (fuer Tests/Debug).
     */
    Servo& getServo() {
        return _tiltServo;
    }
};

#endif  // TILT_H
