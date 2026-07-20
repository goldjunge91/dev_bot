// MIGRATION STATUS: SUPERSEDED (v2) — replaced by motor_driver.h + motor_driver.c
// Kept for reference only. Do not include this file.
// motor.h — Motor struct for one mecanum wheel channel.
// Instantiate as: Motor motors[4];  // [0]=FL [1]=FR [2]=RL [3]=RR

#ifndef MOTOR_H
#define MOTOR_H

#include "pico/stdlib.h"

#include <stdint.h>

/**
 * @brief Describes one motor channel: PWM output, H-bridge direction pins,
 *        and quadrature encoder inputs.
 */
typedef struct {
    uint pwm_pin;    ///< GPIO pin connected to motor driver PWM input
    uint dir_pin_a;  ///< GPIO pin connected to H-bridge IN1 (direction A)
    uint dir_pin_b;  ///< GPIO pin connected to H-bridge IN2 (direction B)

    volatile int32_t enc_count;  ///< Cumulative encoder tick count (updated by GPIO IRQ)
    int32_t prev_enc;            ///< Snapshot from last PID update cycle

    uint enc_pin_a;  ///< Encoder channel A (edge-triggered interrupt)
    uint enc_pin_b;  ///< Encoder channel B (direction sense, polled in IRQ)

    int32_t target_ticks_per_loop;  ///< Velocity setpoint sent by the host [ticks/loop]
    float integral;                 ///< PID integral accumulator
    float prev_error;               ///< PID derivative term memory
} Motor;

#endif  // MOTOR_H
