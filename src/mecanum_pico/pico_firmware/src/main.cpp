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
// NOTE: Do NOT include pico/stdlib.h here — arduino-pico (Earle Philhower)
//       provides get_absolute_time(), make_timeout_time_ms(), sleep_ms() etc.
//       via Arduino.h without needing the full Pico SDK stdio stack.
//
// WICHTIG: Alle Protokoll-Antworten laufen ueber Serial.printf(), NICHT ueber
// nacktes printf(). Beim arduino-pico-Core geht stdout an DEBUG_RP2040_PORT
// (standardmaessig deaktiviert) — nacktes printf() wuerde die Antworten
// stillschweigend verwerfen und die Firmware wirkt "tot" (genau dieser Bug
// hat die v2-Erstinbetriebnahme gekostet).

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
  int v[4] = {0, 0, 0, 0};

  // ---- m: MOTOR_SPEEDS — set PID target ticks/frame ----
  if (buf[0] == 'm') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      raw_pwm_mode = false;
      for (int i = 0; i < 4; i++) {
        motors_pid[i].target = (double)v[i];
      }
      moving = (v[0] || v[1] || v[2] || v[3]) ? 1 : 0;
      last_motion_cmd = get_absolute_time();
    } else {Serial.printf("ERR\n");}

    // ---- o: MOTOR_RAW_PWM — bypass PID ----
  } else if (buf[0] == 'o') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      raw_pwm_mode = true;
      moving = 0;
      motor_set_all(v[0], v[1], v[2], v[3]);
      last_motion_cmd = get_absolute_time();
      Serial.printf("OK\n");
    } else {Serial.printf("ERR\n");}

    // ---- e: READ_ENCODERS ----
  } else if (buf[0] == 'e') {
    Serial.printf(
      "e %ld %ld %ld %ld\n",
      (long)encoder_read(0), (long)encoder_read(1),
      (long)encoder_read(2), (long)encoder_read(3));

    // ---- r: RESET_ENCODERS + PID ----
  } else if (buf[0] == 'r') {
    encoder_reset_all();
    moving = 0;
    raw_pwm_mode = false;
    motor_stop_all();
    pid_reset();
    Serial.printf("OK\n");

    // ---- u: UPDATE_PID gains ----
  } else if (buf[0] == 'u') {
    if (sscanf(buf + 1, "%d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
      Kp = v[0]; Kd = v[1];
      Ki = v[2]; Ko = v[3];
      Serial.printf("OK\n");
    } else {Serial.printf("ERR\n");}

    // ---- b: GET_BAUDRATE ----
  } else if (buf[0] == 'b') {
    Serial.printf("%d\n", BAUD_RATE);

    // ---- i: READ_IMU ----
  } else if (buf[0] == 'i') {
    ImuData d;
    if (imu_read(&d)) {
      Serial.printf(
        "%.4f %.4f %.4f %.4f %.4f %.4f\n",
        (double)d.ax, (double)d.ay, (double)d.az,
        (double)d.gx, (double)d.gy, (double)d.gz);
    } else {Serial.printf("IMU_ERROR\n");}

    // ---- p: PING ----
  } else if (buf[0] == 'p') {
    Serial.printf("0\n");

  } else {Serial.printf("ERR\n");}
}

// ---------------------------------------------------------------------------
// Boot banner — factored out so it can be reprinted on every new USB
// connection (see loop()), not just once at power-on. A monitor opened
// after boot has almost always missed the setup()-time print: USB
// enumeration + host-side reconnect takes longer than the 500ms window
// below, so the banner is sent into the void before anyone is listening.
// ---------------------------------------------------------------------------
static void print_banner()
{
  Serial.printf("\n=== %s ===\n", FW_NAME);
  Serial.printf("Features: %s\n", FW_FEATURES);
  Serial.printf(
    "Baud: %d | PID: Kp=%d Kd=%d Ki=%d Ko=%d | AutoStop: %dms\n",
    BAUD_RATE, DEFAULT_KP, DEFAULT_KD, DEFAULT_KI, DEFAULT_KO, AUTO_STOP_MS);
}

static bool usb_was_connected = false;

// ---------------------------------------------------------------------------
// setup() — runs once after boot
// Do NOT call stdio_init_all() — Arduino framework handles USB-CDC init.
// Boot banner via Serial.printf; die printf-Diagnose der SDK-Libs (IMU) geht
// ueber DEBUG_RP2040_PORT=Serial (siehe platformio.ini build_flags).
// ---------------------------------------------------------------------------
void setup()
{
  Serial.begin(BAUD_RATE);
  sleep_ms(500);    // Wait for USB-CDC enumeration on host

  print_banner();

  motor_init_all();
  encoder_init_all();
  pid_reset();
  imu_setup();

  last_motion_cmd = get_absolute_time();
  next_pid = make_timeout_time_ms(PID_PERIOD_MS);
  usb_was_connected = (bool)Serial;   // don't reprint immediately if a monitor is already attached
}

// ---------------------------------------------------------------------------
// loop() — runs repeatedly after setup()
// ---------------------------------------------------------------------------
void loop()
{
  // ---- Reprint banner on every new USB connection (DTR rising edge) ----
  bool usb_connected = (bool)Serial;
  if (usb_connected && !usb_was_connected) {
    print_banner();
  }
  usb_was_connected = usb_connected;

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
