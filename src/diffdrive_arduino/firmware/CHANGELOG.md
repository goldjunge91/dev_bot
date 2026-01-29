# Changelog

## [1.1.0] - 2026-01-29

### Added
- **Pi Pico (RP2040) Support** - Firmware now compiles and runs on both Arduino Nano and Raspberry Pi Pico
- **TB6612 Motor Driver** - Added support for TB6612FNG motor driver (in addition to L298N)
- Platform-specific pin definitions in `encoder_driver.h` and `motor_driver.h`

### Changed
- Renamed `index` variable to `idx` to avoid ARM compiler conflict
- Fixed `NULL` to `'\0'` for char assignments (C++ compliance)
- Added `return 0` to `runCommand()` function
- Fixed `strtok_r` comparison from `'\0'` to `NULL`

### Pi Pico Default Pins

**Encoder:**
| Encoder | Pin A | Pin B |
|---------|-------|-------|
| Links | GP22 | GP21 |
| Rechts | GP11 | GP10 |

**Motor (TB6612):**
| Funktion | Pin |
|----------|-----|
| LEFT_PWM | GP2 |
| LEFT_IN1 | GP3 |
| LEFT_IN2 | GP4 |
| RIGHT_PWM | GP6 |
| RIGHT_IN1 | GP7 |
| RIGHT_IN2 | GP8 |

---

## [1.0.0] - Original

### Features
- Based on [ros_arduino_bridge by Josh Newans](https://github.com/joshnewans/ros_arduino_bridge)
- Serial protocol for `diffdrive_arduino` ROS 2 hardware interface
- Encoder reading with quadrature decoding
- PID-based velocity control
- L298N motor driver support
