// MIGRATION STATUS: COMPLETE (v2)
// encoder.h — 4-channel quadrature encoder, pure Pico SDK.
// Ported from ROSArduinoBridge/encoder_driver.ino (ARDUINO_ARCH_RP2040 branch).
// Uses full 4-state quadrature lookup table for noise robustness.

#ifndef ENCODER_H
#define ENCODER_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Motor indices
#define ENC_FL 0
#define ENC_FR 1
#define ENC_RL 2
#define ENC_RR 3

/** Initialise all 4 encoder channels: GPIO pullups + IRQ registration. */
void encoder_init_all(void);

/** Read cumulative tick count for encoder [idx]. Thread-safe (disables IRQ briefly). */
int32_t encoder_read(int idx);

/** Reset one encoder counter to zero. */
void encoder_reset(int idx);

/** Reset all 4 encoder counters to zero. */
void encoder_reset_all(void);

#ifdef __cplusplus
}
#endif

#endif  // ENCODER_H
