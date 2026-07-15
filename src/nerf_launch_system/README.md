# nerf_launch_system

ROS 2 (Humble) `ros2_control` hardware interface + high-level control
node for the Nerf dart launcher mounted on Gubot One. Talks to a Nerf
Arduino microcontroller (firmware FSM) over serial.

## Package contents

- `hardware/` — `NerfSystem`, a `hardware_interface::SystemInterface`
  plugin (`nerf_launch_system/NerfSystem`). Joints: `trigger_joint`
  (tilt, position), `dart_pusher_joint` (shot trigger, velocity),
  `system_arming_joint` (arm/disarm, position).
- `nerf_launch_system/nerf_control_node.py` — high-level node exposing
  a normalized tilt topic and a fire service on top of the raw
  controller topics.
- `description/` — standalone URDF/xacro + meshes for the launcher
  (also included by `gubot_description` for the full robot).
- `firmware/` — Arduino firmware for the Nerf microcontroller.

Real robot integration lives in `gubot_bringup`/`gubot_controller`
(`ros2 launch gubot_bringup launch_all_real.launch.py`), which spawns
this package's controllers and remaps `/trigger_controller/commands`
to `/tilt_controller/commands`. This package's own launch files
(`hardware.launch.py`, `simulate.launch.py`) are for standalone
bring-up/testing of the launcher in isolation.

## Build

```bash
colcon build --symlink-install --packages-select nerf_launch_system
source install/setup.bash
```

## Standalone simulation (Gazebo / Ignition Fortress)

```bash
ros2 launch nerf_launch_system simulate.launch.py
```

## Standalone real hardware

```bash
ros2 launch nerf_launch_system hardware.launch.py port:=/dev/ttyACM0
```

## High-level control API

Topic (subscribed): `/nerf/tilt` (`std_msgs/Float64`) — normalized
tilt position:
- `0.0` = down (`tilt_min`, default `-0.52` rad)
- `0.5` = horizontal (`0.0` rad)
- `1.0` = up (`tilt_max`, default `+0.52` rad)

On startup (1s after the node comes up), the launcher homes to
`init_tilt_norm` (parameter, default `0.5` = horizontal).

Service: `/nerf/fire` (`std_srvs/srv/Trigger`) — triggers a shot. Sends
`shot_power` (parameter, default `10.0` = 10% flywheel power) to the
firmware FSM, which runs the full sequence autonomously
(`SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED`).

### Quick manual test

```bash
# Status
ros2 topic echo /joint_states --once

# Tilt to horizontal, then fully up
ros2 topic pub --once /nerf/tilt std_msgs/msg/Float64 "{data: 0.5}"
ros2 topic pub --once /nerf/tilt std_msgs/msg/Float64 "{data: 1.0}"

# Fire
ros2 service call /nerf/fire std_srvs/srv/Trigger
```

### Direct controller topics (bypasses the high-level node)

```bash
# Tilt to a raw joint angle (rad, clamped to [tilt_min, tilt_max])
ros2 topic pub --once /trigger_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0]}"

# Raw shot power (0-100%); the hardware interface fires once when > 0
ros2 topic pub --once /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [10.0]}"
ros2 topic pub --once /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0]}"

# Arm / disarm
ros2 topic pub --once /arming_controller/commands std_msgs/msg/Float64MultiArray "{data: [1.0]}"
ros2 topic pub --once /arming_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0]}"
```

## Troubleshooting

If Gazebo hangs or you get "Address already in use" on restart:

```bash
pkill -f "ign gazebo"
ros2 daemon stop
```
