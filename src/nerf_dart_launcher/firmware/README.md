# Nerf Launcher Firmware (Arduino Pro Micro)

Arduino firmware for controlling a Nerf dart launcher.

## Hardware

| Component | Pin | Description |
|-----------|-----|-------------|
| ESC Motor 1 | D2 | Left flywheel (0-80%) |
| ESC Motor 2 | D3 | Right flywheel (0-80%) |
| Shot Servo | D4 | 360° continuous (dart pusher) |
| Tilt Servo | D5 | 0-180° (up/down) |
| UART TX | TX1 (D1) | Debug via USB-TTL |
| UART RX | RX1 (D0) | Debug via USB-TTL |

## Commands

| Command | Description |
|---------|-------------|
| `ARM` | Arm the system |
| `DISARM` | Disarm (safe state) |
| `SHOT [0-80]` | Fire with optional power (default: 40%) |
| `ESC <0-80>` | Manual ESC control (armed only) |
| `TILT <0-180>` | Set tilt angle |
| `STOP` | Emergency stop |
| `STATUS` | Get armed state |

## Debug Setup

```bash
# Connect USB-TTL adapter to TX1/RX1
screen /dev/ttyUSB0 115200
```

## ROS 2 Integration

The Arduino connects via USB to the Raspberry Pi. Use the `nerf_launcher_node`:

```bash
ros2 launch robot_nerf_launcher nerf_launcher.launch.py serial_port:=/dev/ttyACM0
```

Topics:
- `/nerf_launcher/cmd/arm` (Bool) - ARM/DISARM
- `/nerf_launcher/cmd/fire` (Bool) - Fire sequence
- `/nerf_launcher/cmd/tilt` (Float32) - Tilt angle
- `/nerf_launcher/cmd/power` (Float32) - Shot power 0-80%
