// MIGRATION STATUS: COMPLETE (v2)
// mecanum_controller.c — PID velocity controller for 4-wheel mecanum drive.
// Ported from ROSArduinoBridge/diff_controller.h logic, extended to 4 motors.

#include "mecanum_controller.h"

#include "board_config.h"
#include "encoder_driver.h"
#include "motor_driver.h"

// ---------------------------------------------------------------------------
// Global state
// ---------------------------------------------------------------------------
SetPointInfo motors_pid[4];

int Kp = DEFAULT_KP;
int Kd = DEFAULT_KD;
int Ki = DEFAULT_KI;
int Ko = DEFAULT_KO;

unsigned char moving = 0;

// ---------------------------------------------------------------------------
// pid_reset — zero all PID state; snapshot current encoder values
// Call when going stop→move, on 'r' command, or on auto-stop.
// ---------------------------------------------------------------------------
void pid_reset(void) {
    for (int i = 0; i < 4; i++) {
        motors_pid[i].target = 0.0;
        motors_pid[i].encoder = encoder_read(i);
        motors_pid[i].prev_enc = motors_pid[i].encoder;
        motors_pid[i].output = 0;
        motors_pid[i].prev_input = 0;
        motors_pid[i].iterm = 0;
    }
}

// ---------------------------------------------------------------------------
// doPID — one PID step for a single motor (internal)
// Standard Positional PID — Output = (Kp*e + Ki*∑e - Kd*d(input)) / Ko
// FIX: Removed `output += p->output` which caused runaway accumulation.
//      The old ROSArduinoBridge code accumulated the PID output into itself,
//      effectively making it an integrating controller on top of the PID.
// ---------------------------------------------------------------------------
static void do_pid(SetPointInfo *p) {
    int input = (int)(p->encoder - p->prev_enc);
    long perror = (long)(p->target) - input;

    // Brett Beauregard derivative-kick fix: use -Kd*(input - PrevInput)
    long output = (Kp * perror - Kd * (input - p->prev_input) + p->iterm) / Ko;
    p->prev_enc = p->encoder;

    // FIX: Direktzuweisung statt Akkumulation (output += p->output waere ein Bug)

    // Clamp and conditional integral accumulation (anti-windup)
    if (output >= MAX_PWM) {
        output = MAX_PWM;
    } else if (output <= -MAX_PWM) {
        output = -MAX_PWM;
    } else {
        // Only accumulate ITerm when not saturated (tuning-change fix)
        p->iterm += Ki * perror;
    }

    // Direct assignment — NOT accumulation (p->output = output, NOT +=)
    p->output = output;
    p->prev_input = input;
}

// ---------------------------------------------------------------------------
// pid_update — read all encoders, run PID, set motor outputs
// Call at PID_RATE_HZ (30 Hz).
// ---------------------------------------------------------------------------
void pid_update(void) {
    // Read all encoders first
    for (int i = 0; i < 4; i++) {
        motors_pid[i].encoder = encoder_read(i);
    }

    if (!moving) {
        // Reset once when stopping to prevent startup spikes
        // (PrevInput == 0 means reset already happened)
        int any_prev = 0;
        for (int i = 0; i < 4; i++) {
            if (motors_pid[i].prev_input != 0) {
                any_prev = 1;
                break;
            }
        }
        if (any_prev) {
            pid_reset();
        }
        return;
    }

    // Run PID for each motor and apply output
    for (int i = 0; i < 4; i++) {
        do_pid(&motors_pid[i]);
        motor_set_speed(i, (int)motors_pid[i].output);
    }
}
