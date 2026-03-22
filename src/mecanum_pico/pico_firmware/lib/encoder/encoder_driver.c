// MIGRATION STATUS: COMPLETE (v2)
// encoder.c — 4-channel quadrature decoder, pure Pico SDK.

#include "encoder_driver.h"
#include "board_config.h"
#include "hardware/gpio.h"
#include "pico/critical_section.h"
#include <stdint.h>

// ---------------------------------------------------------------------------
// Quadrature state lookup table (from ROSArduinoBridge/encoder_driver.ino)
// Index = (prev_state << 2) | curr_state;  value = +1, -1, or 0
// ---------------------------------------------------------------------------
static const int8_t QEM[16] = {
    0, +1, -1,  0,
   -1,  0,  0, +1,
   +1,  0,  0, -1,
    0, -1, +1,  0
};

// Pin tables
static const uint ENC_A_PINS[4] = { FL_ENC_A_PIN, FR_ENC_A_PIN, RL_ENC_A_PIN, RR_ENC_A_PIN };
static const uint ENC_B_PINS[4] = { FL_ENC_B_PIN, FR_ENC_B_PIN, RL_ENC_B_PIN, RR_ENC_B_PIN };

// State & counters
static volatile int32_t enc_count[4] = { 0, 0, 0, 0 };
static volatile uint8_t enc_last[4] = { 0, 0, 0, 0 };

static critical_section_t enc_cs;

// ---------------------------------------------------------------------------
// Shared GPIO IRQ handler — all 8 encoder pins route here
// ---------------------------------------------------------------------------
static void encoder_irq_handler(uint gpio, uint32_t events)
{
    (void)events;
    for (int i = 0; i < 4; i++) {
        if (gpio == ENC_A_PINS[i] || gpio == ENC_B_PINS[i]) {
            uint8_t a = gpio_get(ENC_A_PINS[i]) ? 1u : 0u;
            uint8_t b = gpio_get(ENC_B_PINS[i]) ? 1u : 0u;
            uint8_t curr = (a << 1) | b;
            uint8_t idx = (enc_last[i] << 2) | curr;
            enc_count[i] += QEM[idx & 0x0F];
            enc_last[i] = curr;
        }
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

void encoder_init_all(void)
{
    critical_section_init(&enc_cs);

    for (int i = 0; i < 4; i++) {
        // Configure A and B pins as inputs with pull-ups
        gpio_init(ENC_A_PINS[i]);
        gpio_set_dir(ENC_A_PINS[i], GPIO_IN);
        gpio_pull_up(ENC_A_PINS[i]);

        gpio_init(ENC_B_PINS[i]);
        gpio_set_dir(ENC_B_PINS[i], GPIO_IN);
        gpio_pull_up(ENC_B_PINS[i]);

        // Capture initial state
        uint8_t a = gpio_get(ENC_A_PINS[i]) ? 1u : 0u;
        uint8_t b = gpio_get(ENC_B_PINS[i]) ? 1u : 0u;
        enc_last[i] = (a << 1) | b;

        // Register IRQ on both edges of both channels
        gpio_set_irq_enabled_with_callback(
            ENC_A_PINS[i],
            GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL,
            true,
            encoder_irq_handler);
        gpio_set_irq_enabled(
            ENC_B_PINS[i],
            GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL,
            true);
    }
}

int32_t encoder_read(int idx)
{
    if (idx < 0 || idx >= 4) return 0;
    critical_section_enter_blocking(&enc_cs);
    int32_t val = enc_count[idx];
    critical_section_exit(&enc_cs);
    return val;
}

void encoder_reset(int idx)
{
    if (idx < 0 || idx >= 4) return;
    critical_section_enter_blocking(&enc_cs);
    enc_count[idx] = 0;
    critical_section_exit(&enc_cs);
}

void encoder_reset_all(void)
{
    critical_section_enter_blocking(&enc_cs);
    for (int i = 0; i < 4; i++) enc_count[i] = 0;
    critical_section_exit(&enc_cs);
}
