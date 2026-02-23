//
// Created by tozzi on 18.02.2026.
//

#ifndef FIRINGFSM_H
#define FIRINGFSM_H

#include <Arduino.h>

#include "../../include/Config.h"

/**
 * @brief States of the firing sequence.
 */
enum class FiringState {
    IDLE, ///< System ready, motor off
    ARMING, ///< Safety delay before arming
    ARMED, ///< System active, ready to fire
    DISARMING, ///< Safety delay/action before idle
    DISARMED, ///< Safe state, inputs ignored
    SPINNING_UP, ///< Flywheels accelerating
    PUSHING, ///< Pusher servo extending to feed dart
    BRAKING, ///< Pusher servo retracting/braking
    COOLDOWN, ///< Brief pause after shot
    ESC_TEST, ///< Manual flywheel speed test
    CALIBRATING ///< ESC calibration mode
};

// Callback-Typen (Function Pointers)
typedef void (*SimpleCallback)();

typedef void (*EscCallback)(int powerPercent);

typedef void (*ServoCallback)(int microseconds);

typedef void (*DebugCallback)(const char *msg);

/**
 * @brief Finite State Machine for the Nerf Launcher.
 *
 * Manages the complex timing and state transitions for firing darts safely.
 * Decouples logic from hardware implementation via callbacks.
 */
class FiringFSM {
private:
    FiringState _currentState;
    FiringState _nextState;

    uint32_t _stateStartTime;
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
     * @brief Constructor
     *
     * @param onFlywheelPower Callback to set ESC power (0-100).
     * @param onShotServo Callback to set pusher servo position (us).
     * @param onAttachESCs Callback to attach ESC pins.
     * @param onDetachESCs Callback to detach ESC pins.
     * @param onAttachShot Callback to attach pusher servo.
     * @param onDetachShot Callback to detach pusher servo.
     * @param onDebug Callback for debug strings.
     */
    FiringFSM(EscCallback onFlywheelPower, ServoCallback onShotServo,
              SimpleCallback onAttachESCs, SimpleCallback onDetachESCs,
              SimpleCallback onAttachShot, SimpleCallback onDetachShot,
              DebugCallback onDebug);

    /**
     * @brief Evaluates time-based or logic-based state transitions.
     * Call this in the main loop.
     */
    void evalTransition();

    /**
     * @brief Executes actions based on the current state.
     * Call this in the main loop after evalTransition().
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

#endif // FIRINGFSM_H
