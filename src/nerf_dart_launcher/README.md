# Robot Nerf Launcher

ROS 2 package for controlling a Nerf dart launcher via Arduino Pro Micro.

## Architecture

```
ROS 2 Topics → nerf_launcher_node.py → USB Serial → Arduino Pro Micro → ESCs + Servos
```

## Installation

```bash
# Build
colcon build --packages-select nerf_dart_launcher

# Source
source install/setup.bash
```

## Usage

```bash
# Start the node
ros2 launch nerf_dart_launcher nerf_launcher.launch.py

# With custom serial port
ros2 launch nerf_dart_launcher nerf_launcher.launch.py serial_port:=/dev/ttyACM1
```

## ROS Topics

| Topic              | Type      | Description                  |
| ------------------ | --------- | ---------------------------- |
| `cmd/arm`          | `Bool`    | `true`=ARM, `false`=DISARM   |
| `cmd/fire`         | `Bool`    | `true`=execute shot sequence |
| `cmd/tilt`         | `Float32` | Tilt angle 0-180°            |
| `cmd/power`        | `Float32` | Shot power 0-80%             |
| `status/armed`     | `Bool`    | Current armed state          |
| `status/connected` | `Bool`    | Serial connection status     |

## Parameters

| Parameter     | Default        | Description         |
| ------------- | -------------- | ------------------- |
| `serial_port` | `/dev/ttyACM0` | Arduino serial port |
| `baud_rate`   | `115200`       | Serial baud rate    |

## Firmware

Arduino firmware is in the `firmware/` directory. See [firmware/README.md](firmware/README.md).

## Quick Test

```bash
ros2 topic pub --once /nerf_launcher/cmd/arm std_msgs/msg/Bool "data: true"
ros2 topic pub --once /nerf_launcher/cmd/tilt std_msgs/msg/Float32 "data: 45.0"
ros2 topic pub --once /nerf_launcher/cmd/fire std_msgs/msg/Bool "data: true"
ros2 topic pub --once /nerf_launcher/cmd/arm std_msgs/msg/Bool "data: false"
```
