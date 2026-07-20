# mecanum_pico Firmware (v2)

Firmware for the Raspberry Pi Pico (RP2040) — 4-wheel mecanum drive.
Motor driver: **TB6612FNG** · IMU: **ICM-20948** (SPI) · Interface: **USB-CDC serial**

---

## Feature Overview

| Feature                                          | Status  |
| ------------------------------------------------ | ------  |
| 4× TB6612 motor channels (FL/FR/RL/RR)           | ✅      |
| 4× Quadrature encoder (QEM lookup table)         | ✅      |
| 4× PID velocity controller (derivative-kick fix) | ✅      |
| ICM-20948 IMU via SPI (accel + gyro)             | ✅      |
| Auto-stop watchdog (2000 ms default)             | ✅      |
| Raw PWM mode (`o` command)                       | ✅      |
| Runtime PID tuning (`u` command)                 | ✅      |
| Boot banner + degraded-mode IMU fallback         | ✅      |

---

## Serial Command Reference

All commands are CR (`\r`) or LF (`\n`) terminated. Response always ends with `\n`.

| Command   | Format            | Response              | Description                                      |
| --------- | ----------------- | --------------------- | ------------------------------------------------ |
| `m`       | `m fl fr rl rr\r` | *(silent)*            | Set PID target [ticks/frame] for all 4 motors    |
| `o`       | `o fl fr rl rr\r` | `OK\n`                | Raw PWM [-255..255]; disables PID until next `m` |
| `e`       | `e\r`             | `e fl fr rl rr\n`     | Read cumulative encoder ticks                    |
| `r`       | `r\r`             | `OK\n`                | Reset encoders + PID state + stop motors         |
| `u`       | `u Kp Kd Ki Ko\r` | `OK\n`                | Update PID gains at runtime                      |
| `b`       | `b\r`             | `115200\n`            | Get baud rate (informational)                    |
| `i`       | `i\r`             | `ax ay az gx gy gz\n` | Read IMU (accel [g], gyro [dps])                 |
| `i`       | `i\r`             | `IMU_ERROR\n`         | IMU not initialised or read failed               |
| `p`       | `p\r`             | `0\n`                 | Ping / keepalive                                 |
| *unknown* |                   | `ERR\n`               | Parse error                                      |

### Auto-Stop

If no `m` or `o` command is received for **2000 ms**, all motors stop and PID resets silently.
Configurable via `AUTO_STOP_MS` in `board_config.h`.

---

## Wiring — TB6612 Motor Driver

| Motor       | Index | PWM Pin | IN1 Pin | IN2 Pin | Enc A | Enc B |
| ----------- | ----- | ------- | ------- | ------- | ----- | ----- |
| Front-Left  | 0     | GP2     | GP3     | GP4     | GP5   | GP6   |
| Front-Right | 1     | GP7     | GP8     | GP9     | GP10  | GP11  |
| Rear-Left   | 2     | GP12    | GP13    | GP14    | GP15  | GP16* |
| Rear-Right  | 3     | GP17*   | GP18*   | GP19*   | GP20  | GP21  |

> **\* Pin conflict warning:** GP16–GP19 overlap with the default IMU SPI0 pins.
> If using both RL/RR motors and the ICM-20948 simultaneously, remap either
> the motor pins or use SPI1 (e.g. GP22/CS, GP26/SCK, GP27/MOSI, GP28/MISO).
> Edit `board_config.h` — both tables are clearly commented.

**TB6612 STBY pin:** Wire to 3.3 V, or define `TB6612_STBY_PIN` in `board_config.h`
to let the firmware drive it HIGH on startup.

---

## Wiring — ICM-20948 IMU (SPI0 default)

| Signal | Pico GPIO | ICM-20948 pin |
| ------ | --------- | ------------- |
| CS     | GP17      | NCS           |
| SCK    | GP18      | SCLK / SCL    |
| MOSI   | GP19      | SDI           |
| MISO   | GP16      | ADA / SDO     |
| VCC    | 3.3 V     | VDD           |
| GND    | GND       | GND           |

To change pins: edit `IMU_CS_PIN`, `IMU_SCK_PIN`, `IMU_MOSI_PIN`, `IMU_MISO_PIN`,
and `IMU_SPI_PORT` in `board_config.h`.

---

## Building

```bash
# Prerequisites: Pico SDK installed, PICO_SDK_PATH set
cd mecanum_pico/pico_firmware
mkdir build && cd build
cmake ..
make -j4
# Flash: copy mecanum_pico_firmware.uf2 to Pico (hold BOOTSEL while plugging in)
```

---

## PID Tuning

Default gains (from ROSArduinoBridge): `Kp=20  Kd=12  Ki=0  Ko=50`

Runtime update without reflashing:

```txt
u 20 12 0 50\r
```

Start with `Ki=0`. Increase `Kp` until oscillation, then back off.
Add `Kd` only if overshoot is a problem. `Ko` scales final output — increase
to reduce sensitivity if PWM saturates at low speeds.

---

## udev Rule (Linux host)

```bash
SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", SYMLINK+="pico_mecanum"
```

Save to `/etc/udev/rules.d/99-pico-mecanum.rules`, then:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## Troubleshooting

| Symptom                        | Likely cause           | Fix                                                             |
| ------------------------------ | ---------------------- | --------------------------------------------------------------- |
| `IMU_ERROR` on `i`             | Wiring / pin conflict  | Check SPI pins vs motor pins in `board_config.h`                |
| Motor spins wrong direction    | `MOTOR_REVERSE[]`      | Set `1` for affected index in `motor_driver.c`                  |
| Encoder counts wrong direction | Swap ENC_A / ENC_B     | Swap A and B pin defines in `board_config.h`                    |
| Robot spins on strafe          | FL/RR or FR/RL swapped | Verify motor index mapping matches physical layout              |
| No USB serial output           | stdio_usb not ready    | Add `sleep_ms(500)` after `stdio_init_all()` (already included) |
