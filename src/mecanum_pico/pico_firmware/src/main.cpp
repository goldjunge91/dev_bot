// MIGRATION STATUS: COMPLETE (v2 — PlatformIO Arduino framework)
// main.cpp — mecanum_pico firmware, full command set.
// Framework: Arduino (Earle Philhower arduino-pico), Board: Raspberry Pi Pico
// Pico SDK functions are fully accessible under Arduino-Pico framework.
//
// Command reference (CR or LF terminated):
//   m <fl> <fr> <rl> <rr>  — set PID targets [ticks/frame] → (silent)
//   o <fl> <fr> <rl> <rr>  — raw PWM [-255..255]           → "OK\n"
//   e                      — read encoders                  → "e fl fr rl rr\n"
//   r                      — reset encoders + PID + stop    → "OK\n"
//   u <kp> <kd> <ki> <ko>  — update PID gains              → "OK\n"
//   b                      — get baud rate                  → "<baud>\n"
//   i                      — read IMU                       → "ax ay az gx gy gz\n"
//   p                      — ping                           → "0\n"
//   unknown                                                 → "ERR\n"

#include <Arduino.h>
// NOTE: Do NOT include pico/stdlib.h here — framework-arduino-mbed provides
//       get_absolute_time(), make_timeout_time_ms(), sleep_ms() etc. via
//       Arduino.h without needing the full Pico SDK stdio stack.

#include "board_config.h"
#include "motor_driver.h"
#include "encoder_driver.h"
#include "mecanum_controller.h"
#include "imu_driver.h"

#include <stdint.h>
#include <stdio.h>

// ---------------------------------------------------------------------------
// File-scope state
// ---------------------------------------------------------------------------
static absolute_time_t last_motion_cmd;
static bool raw_pwm_mode = false;

static char rx_buf[64];
static int rx_pos = 0;
static absolute_time_t next_pid;

static const uint32_t PID_PERIOD_MS = 1000u / PID_RATE_HZ;

// ---------------------------------------------------------------------------
// Command handler (called when a complete line is received)
// ---------------------------------------------------------------------------
static void handle_command(const char * buf)
{
  int32_t v[4] = {0, 0, 0, 0};

  // ---- m: MOTOR_SPEEDS — set PID target ticks/frame ----
  if (buf[0] == 'm') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      raw_pwm_mode = false;
      for (int i = 0; i < 4; i++) {
        motors_pid[i].target = (double)v[i];
      }
      moving = (v[0] || v[1] || v[2] || v[3]) ? 1 : 0;
      last_motion_cmd = get_absolute_time();
    } else {printf("ERR\n");}

    // ---- o: MOTOR_RAW_PWM — bypass PID ----
  } else if (buf[0] == 'o') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      raw_pwm_mode = true;
      moving = 0;
      motor_set_all((int)v[0], (int)v[1], (int)v[2], (int)v[3]);
      last_motion_cmd = get_absolute_time();
      printf("OK\n");
    } else {printf("ERR\n");}

    // ---- e: READ_ENCODERS ----
  } else if (buf[0] == 'e') {
    printf(
      "e %d %d %d %d\n",
      (int)encoder_read(0), (int)encoder_read(1),
      (int)encoder_read(2), (int)encoder_read(3));

    // ---- r: RESET_ENCODERS + PID ----
  } else if (buf[0] == 'r') {
    encoder_reset_all();
    moving = 0;
    raw_pwm_mode = false;
    motor_stop_all();
    pid_reset();
    printf("OK\n");

    // ---- u: UPDATE_PID gains ----
  } else if (buf[0] == 'u') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      Kp = (int)v[0]; Kd = (int)v[1];
      Ki = (int)v[2]; Ko = (int)v[3];
      printf("OK\n");
    } else {printf("ERR\n");}

    // ---- b: GET_BAUDRATE ----
  } else if (buf[0] == 'b') {
    printf("%d\n", BAUD_RATE);

    // ---- i: READ_IMU ----
  } else if (buf[0] == 'i') {
    ImuData d;
    if (imu_read(&d)) {
      printf(
        "%.4f %.4f %.4f %.4f %.4f %.4f\n",
        (double)d.ax, (double)d.ay, (double)d.az,
        (double)d.gx, (double)d.gy, (double)d.gz);
    } else {printf("IMU_ERROR\n");}

    // ---- p: PING ----
  } else if (buf[0] == 'p') {
    printf("0\n");

  } else {printf("ERR\n");}
}

// ---------------------------------------------------------------------------
// setup() — runs once after boot
// Arduino-Pico routes printf() to USB Serial after Serial.begin().
// Do NOT call stdio_init_all() — Arduino framework handles stdio init.
// ---------------------------------------------------------------------------
void setup()
{
  Serial.begin(BAUD_RATE);
  sleep_ms(500);    // Wait for USB-CDC enumeration on host

  // Boot banner via printf (routed to USB Serial by Arduino-Pico)
  printf("\n=== %s ===\n", FW_NAME);
  printf("Features: %s\n", FW_FEATURES);
  printf(
    "Baud: %d | PID: Kp=%d Kd=%d Ki=%d Ko=%d | AutoStop: %dms\n",
    BAUD_RATE, DEFAULT_KP, DEFAULT_KD, DEFAULT_KI, DEFAULT_KO, AUTO_STOP_MS);

  motor_init_all();
  encoder_init_all();
  pid_reset();
  imu_setup();

  last_motion_cmd = get_absolute_time();
  next_pid = make_timeout_time_ms(PID_PERIOD_MS);
}

// ---------------------------------------------------------------------------
// loop() — runs repeatedly after setup()
// ---------------------------------------------------------------------------
void loop()
{
  // ---- Non-blocking serial receive via Arduino Serial ----
  // (replaces getchar_timeout_us under Arduino framework)
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (rx_pos > 0) {
        rx_buf[rx_pos] = '\0';
        handle_command(rx_buf);
        rx_pos = 0;
      }
    } else if (rx_pos < (int)(sizeof(rx_buf) - 1)) {
      rx_buf[rx_pos++] = c;
    }
  }

  // ---- Auto-stop watchdog ----
  int64_t since_cmd_ms =
    absolute_time_diff_us(last_motion_cmd, get_absolute_time()) / 1000;
  if (since_cmd_ms > AUTO_STOP_MS && (moving || raw_pwm_mode)) {
    moving = 0;
    raw_pwm_mode = false;
    motor_stop_all();
    pid_reset();
    // (silent — no serial output to avoid host spam)
  }

  // ---- PID update at fixed rate (30 Hz) ----
  if (time_reached(next_pid)) {
    if (!raw_pwm_mode) {
      pid_update();
    }
    next_pid = delayed_by_ms(next_pid, PID_PERIOD_MS);
  }
}
