// MIGRATION STATUS: COMPLETE (v2)
// motor_driver.h — TB6612 4-motor driver API (pure Pico SDK).

#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif

/** Initialise all 4 motor channels (PWM + direction GPIO + optional STBY). */
void motor_init_all(void);

/**
     * @brief Set speed for one motor.
     * @param idx   0=FL  1=FR  2=RL  3=RR
     * @param speed -255..+255  (0 = coast stop)
     */
void motor_set_speed(int idx, int speed);

/** Convenience: set all 4 motors in one call. */
void motor_set_all(int fl, int fr, int rl, int rr);

/** Stop all motors immediately (coast). */
void motor_stop_all(void);

#ifdef __cplusplus
}
#endif

#endif  // MOTOR_DRIVER_H
