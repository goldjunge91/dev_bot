// MIGRATION STATUS: COMPLETE (v2)
// mecanum_controller.h — PID velocity controller for 4-wheel mecanum drive.
// Ported from ROSArduinoBridge/diff_controller.h, extended to 4 independent motors.
// Derivative-kick fix and integral tuning-change fix from Brett Beauregard.

#ifndef MECANUM_CONTROLLER_H
#define MECANUM_CONTROLLER_H

#include "encoder_driver.h"
#include "motor_driver.h"
#include "board_config.h"
#include <stdint.h>

// ---------------------------------------------------------------------------
// PID state for one motor (matches original SetPointInfo)
// ---------------------------------------------------------------------------
typedef struct {
    double target;      ///< Target ticks per PID frame
    int32_t encoder;    ///< Current encoder reading
    int32_t prev_enc;   ///< Encoder reading last frame
    int    prev_input;  ///< Last input (enc delta) — derivative-kick fix
    int    iterm;       ///< Integrated term — tuning-change fix
    long   output;      ///< Last PWM output
} SetPointInfo;

// Global PID state for 4 motors
extern SetPointInfo motors_pid[4];

// Runtime-tunable PID gains (set via 'u' command)
extern int Kp, Kd, Ki, Ko;

// Motion flag: 0 = stopped, 1 = moving
extern unsigned char moving;

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

#ifdef __cplusplus
extern "C" {
#endif

/** Zero all PID state. Call when transitioning from stop → move or on reset. */
void pid_reset(void);

/** Run one PID frame for all 4 motors (call at PID_RATE_HZ). */
void pid_update(void);

#ifdef __cplusplus
}
#endif

#endif  // MECANUM_CONTROLLER_H
