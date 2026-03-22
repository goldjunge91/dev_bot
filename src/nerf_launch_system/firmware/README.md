   # Nerf Launcher Firmware (Arduino Pro Micro)

Arduino firmware for controlling a Nerf dart launcher. This firmware runs on an Arduino Pro Micro (or compatible) and interfaces via USB Serial or UART.

## Hardware Configuration (Config.h)

| Component      | Pin   | Note                                      |
| :------------- | :---- | :---------------------------------------- |
| **ESC Left**   | `D2`  | Flywheel Motor 1 (1000-2000us)            |
| **ESC Right**  | `D3`  | Flywheel Motor 2 (1000-2000us)            |
| **Shot Servo** | `D9`  | Continuous Rotation Servo (Pusher)        |
| **Tilt Servo** | `D10` | 360°/Continuous Servo (Up/Down Mechanism) |
| **UART TX**    | `TX1` | Debug / Alternative Control               |
| **UART RX**    | `RX1` | Debug / Alternative Control               |

> **Note:** Pin mappings are defined in `nerf_micro/Config.h`.

## Command Interface (Comms.h)

The firmware accepts plain-text commands terminated by a newline (`\n` or `\r`).

### System Safety
| Command  | Description                                                 |
| :------- | :---------------------------------------------------------- |
| `ARM`    | Arms the ESCs. System will beep. **Wait 2s** before firing. |
| `DISARM` | Disarms the system immediately. Detaches ESCs.              |
| `STOP`   | Same as `DISARM`. Emergency Stop.                           |
| `STATUS` | Returns `STATUS: ARMED` or `STATUS: DISARMED`.              |

### Firing Control
| Command          | Description                                                            |
| :--------------- | :--------------------------------------------------------------------- |
| `SHOT <pwr>`     | Initiates full firing sequence. `pwr` (0-100) sets flywheel speed.     |
| `TEST_ESC <pwr>` | Spins flywheels ONLY (no pusher) at `pwr` (0-100). Send `STOP` to end. |
| `TEST_SHOT <ms>` | Cycles pusher servo ONLY (no flywheels) for `ms` milliseconds.         |
| `NF`             | "Nudge Forward" - Manually jogs pusher forward.                        |
| `NB`             | "Nudge Back" - Manually jogs pusher backward.                          |

### Tilt Control
*Tilt uses a continuous rotation servo driving a lead screw or gear.*

| Command   | Description                            |
| :-------- | :------------------------------------- |
| `UP <ms>` | Moves tilt UP for `ms` milliseconds.   |
| `DN <ms>` | Moves tilt DOWN for `ms` milliseconds. |
| `TU`      | "Tilt Up" - Small nudge up.            |
| `TD`      | "Tilt Down" - Small nudge down.        |

### Configuration & Calibration
| Command         | Description                                                     |
| :-------------- | :-------------------------------------------------------------- |
| `CAL`           | enters **ESC Calibration Mode**. (See below)                    |
| `SAVE`          | Prints current configuration settings.                          |
| `PWM <us>`      | Sends raw PWM commands (1000-2000) to ESCs.                     |
| `ZERO_S <us>`   | Sets the "Neutral" pulse width for the Shot/Pusher servo.       |
| `ZERO_T <us>`   | Sets the "Neutral" pulse width for the Tilt servo.              |
| `SET_SHOT <ms>` | Sets the duration of the firing cycle (pusher activation time). |

---

## ESC Calibration Procedure (`CAL`)

1. Ensure battery is **DISCONNECTED**.
2. Connect USB and open Serial Monitor.
3. Send `CAL`.
   - Firmware will output: `WARNING: CALIBRATION MODE - MAX THROTTLE`
4. Connect the main battery (LiPo) to the ESCs.
   - You should hear the specific "Calibration Beep" sequence from the ESCs.
5. Immediately send `STOP` (or `DISARM`).
   - This sends the MIN throttle signal to finish calibration.
   - ESCs should beep again to confirm.

## Tuning & Neutral Points

Since continuous rotation servos vary, you may need to tune the "Zero" (Stop) point so they don't drift.

1. **Shot Servo:** If the pusher drifts, use `ZERO_S <us>` (default ~1430) until it stops completely.
2. **Tilt Servo:** If the tilt mechanism drifts, use `ZERO_T <us>` (default ~1430) until it stops completely.
3. **Save:** Use `SAVE` to view your tuned values (Note: Values are currently reset on reboot unless hardcoded in `Config.h`. *Use `Config.h` to make permanent changes.*)

## ROS 2 Integration

The Arduino connects via USB to the Raspberry Pi. Use the `nerf_launcher_node`:

```bash
ros2 launch nerf_dart_launcher nerf_launcher.launch.py serial_port:=/dev/ttyACM0
```

Topics:
- `/nerf_launcher/cmd/arm` (Bool) - ARM/DISARM
- `/nerf_launcher/cmd/fire` (Bool) - Fire sequence
- `/nerf_launcher/cmd/tilt` (Float32) - Tilt angle
- `/nerf_launcher/cmd/power` (Float32) - Shot power 0-80%
