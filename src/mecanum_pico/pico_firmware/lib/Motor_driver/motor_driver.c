// MIGRATION STATUS: COMPLETE (v2 — TB6612, 4 motors, pure Pico SDK)
// motor_driver.c — TB6612 motor driver for 4 mecanum wheel channels.
// Ported from ROSArduinoBridge/motor_driver.ino (TB6612_MOTOR_DRIVER + ARDUINO_ARCH_RP2040).
// No Arduino.h — uses pico/stdlib.h + hardware/pwm.h + hardware/gpio.h only.

#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "motor_driver.h"
#include "board_config.h"   // PlatformIO: include/ is in build path automatically
#include "hardware/pwm.h"
#include <stdint.h>

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

// Pin table: indexed by motor index [0..3]
static const uint8_t PWM_PINS[4] = { FL_PWM_PIN, FR_PWM_PIN, RL_PWM_PIN, RR_PWM_PIN };
static const uint8_t IN1_PINS[4] = { FL_IN1_PIN, FR_IN1_PIN, RL_IN1_PIN, RR_IN1_PIN };
static const uint8_t IN2_PINS[4] = { FL_IN2_PIN, FR_IN2_PIN, RL_IN2_PIN, RR_IN2_PIN };

// Per-motor reverse flag (set 1 to invert direction for that motor)
static const uint8_t MOTOR_REVERSE[4] = { 0, 0, 0, 0 };

static void pwm_init_pin(uint pin)
{
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(pin);
    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_clkdiv(&cfg, PWM_CLK_DIV);
    pwm_config_set_wrap(&cfg, PWM_WRAP);
    pwm_init(slice, &cfg, true);
    // Start at 0
    pwm_set_chan_level(slice, pwm_gpio_to_channel(pin), 0);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

void motor_init_all(void)
{
#ifdef TB6612_STBY_PIN
    gpio_init(TB6612_STBY_PIN);
    gpio_set_dir(TB6612_STBY_PIN, GPIO_OUT);
    gpio_put(TB6612_STBY_PIN, 1);  // Enable driver
#endif

    for (int i = 0; i < 4; i++) {
        // Direction pins
        gpio_init(IN1_PINS[i]);
        gpio_set_dir(IN1_PINS[i], GPIO_OUT);
        gpio_put(IN1_PINS[i], 0);

        gpio_init(IN2_PINS[i]);
        gpio_set_dir(IN2_PINS[i], GPIO_OUT);
        gpio_put(IN2_PINS[i], 0);

        // PWM pin
        pwm_init_pin(PWM_PINS[i]);
    }
}

/**
 * @brief Set speed for one motor.
 * @param idx   Motor index 0=FL 1=FR 2=RL 3=RR
 * @param speed Signed speed: -MAX_PWM..+MAX_PWM (0 = coast stop)
 */
void motor_set_speed(int idx, int speed)
{
    if (idx < 0 || idx >= 4) return;

    if (MOTOR_REVERSE[idx]) speed = -speed;

    // Clamp
    if (speed > MAX_PWM) speed = MAX_PWM;
    if (speed < -MAX_PWM) speed = -MAX_PWM;

    uint8_t in1 = IN1_PINS[idx];
    uint8_t in2 = IN2_PINS[idx];
    uint8_t pwm_pin = PWM_PINS[idx];

    if (speed == 0) {
        // Coast: both direction pins LOW
        gpio_put(in1, 0);
        gpio_put(in2, 0);
    }
    else if (speed > 0) {
        gpio_put(in1, 1);
        gpio_put(in2, 0);
    }
    else {
        gpio_put(in1, 0);
        gpio_put(in2, 1);
        speed = -speed;
    }

    // 1 µs settling time (from original RP2040 motor_driver.ino)
    sleep_us(1);

    uint slice = pwm_gpio_to_slice_num(pwm_pin);
    pwm_set_chan_level(slice, pwm_gpio_to_channel(pwm_pin), (uint16_t)speed);
}

/** @brief Set all 4 motors at once. */
void motor_set_all(int fl, int fr, int rl, int rr)
{
    motor_set_speed(0, fl);
    motor_set_speed(1, fr);
    motor_set_speed(2, rl);
    motor_set_speed(3, rr);
}

/** @brief Emergency stop — all motors to 0. */
void motor_stop_all(void)
{
    motor_set_all(0, 0, 0, 0);
}
