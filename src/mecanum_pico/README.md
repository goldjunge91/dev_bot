# mecanum_pico

ROS 2 hardware interface for a **4-wheel mecanum drive** robot controlled by a
**Raspberry Pi Pico** via USB-CDC serial.

Refactored from `diffdrive_arduino` (2-wheel diff drive).

---

## Architecture

```
[ Nav2 / Teleop ]
      │  geometry_msgs/TwistStamped (cmd_vel)
      ▼
[ mecanum_drive_controller ]  ← ros2_controllers
      │  velocity commands: FL, FR, RL, RR  (rad/s)
      ▼
[ MecanumPicoHardware ]       ← THIS PACKAGE (SystemInterface)
      │  Serial UART (USB-CDC)  115200 baud
      │  "m <fl> <fr> <rl> <rr>\r"   → Pico (ticks/loop)
      │  "e <fl> <fr> <rl> <rr>\r\n" ← Pico (encoder counts)
      ▼
[ Raspberry Pi Pico ]         ← pico_firmware/
      │  PWM + H-bridge × 4
      ▼
[ 4 × Mecanum Wheels + Encoders ]
```

---

## Package Layout

```
mecanum_pico/
├── hardware/
│   ├── mecanum_pico.cpp                  ← SystemInterface implementation
│   └── include/mecanum_pico/
│       ├── mecanum_pico.hpp              ← Class + Config struct (4 wheels)
│       ├── pico_comms.hpp                ← Serial protocol layer
│       ├── wheel.hpp                     ← Single-wheel data struct
│       └── visibility_control.h
├── bringup/
│   ├── config/mecanum_controllers.yaml   ← mecanum_drive_controller config
│   └── launch/mecanum_pico.launch.py     ← Launch (real + mock hardware)
├── description/
│   └── ros2_control/
│       └── mecanum_pico.ros2_control.xacro  ← 4-joint URDF block
├── pico_firmware/                        ← RP2040 C firmware
│   ├── main.c
│   ├── motor.h
│   ├── board_config.h                    ← GPIO pin assignments
│   ├── CMakeLists.txt
│   └── README.md
└── test/
    ├── test_wheel.cpp                    ← Sprint 1 unit tests
    ├── test_pico_comms.cpp               ← Sprint 2 unit tests
    ├── test_hardware_interface.cpp       ← Sprint 3 plugin load tests
    ├── test_launch.py                    ← Sprint 6 CI launch tests
    └── hil/
        └── test_mecanum_motion.py        ← Sprint 7 HIL motion tests
```

---

## Serial Protocol

| Direction     | Frame                             | Example                        |
|--------------|-----------------------------------|--------------------------------|
| Host → Pico  | `m <fl> <fr> <rl> <rr>\r`        | `m 10 -10 10 -10\r`           |
| Pico → Host  | `e <fl> <fr> <rl> <rr>\r\n`      | `e 1234 -1230 1231 -1228\r\n` |
| Host → Pico  | `e\r` (request)                   | —                              |
| Host → Pico  | `r\r` (reset encoders)            | —                              |
| Pico → Host  | `OK\r\n` (ack for reset)          | —                              |

Values are **signed 32-bit integers** representing cumulative encoder ticks
(feedback) or ticks-per-loop targets (command).

---

## Development

### Building

```bash
cd ~/ros2_ws
colcon build --packages-select mecanum_pico
```

### Running Tests

```bash
# Unit tests only (no hardware required)
colcon test --packages-select mecanum_pico
colcon test-result --verbose

# Individual test binaries (after build):
./build/mecanum_pico/test_wheel
./build/mecanum_pico/test_pico_comms
```

### Running (mock hardware — no Pico needed)

```bash
source install/setup.bash
ros2 launch mecanum_pico mecanum_pico.launch.py use_mock_hardware:=true

# In another terminal — verify 4 interfaces:
ros2 control list_hardware_interfaces
# Expected:
#   command interfaces:
#     front_left_wheel_joint/velocity  [available] [claimed]
#     front_right_wheel_joint/velocity [available] [claimed]
#     rear_left_wheel_joint/velocity   [available] [claimed]
#     rear_right_wheel_joint/velocity  [available] [claimed]
```

### Running (real hardware)

```bash
ros2 launch mecanum_pico mecanum_pico.launch.py
# Pico must be connected; udev rule recommended (see pico_firmware/README.md)
```

---

## Controller Configuration

`bringup/config/mecanum_controllers.yaml` — values marked **MEASURE YOUR ROBOT**
must be calibrated in Sprint 7:

| Parameter | Default | How to calibrate |
|-----------|---------|-----------------|
| `wheels_radius` | 0.05 m | Drive 1 m, compare `/odom` to ground truth |
| `sum_of_robot_center_projection_on_X_Y_axis` | 0.30 m | Command rotation, minimize translation |
| `enc_counts_per_rev` | 1440 | Rotate wheel 1 rev manually, count ticks |

---

## Calibration

See Sprint 7 procedures:

1. **Encoder calibration** — `m 0 0 0 0\r`, rotate each wheel one full revolution,
   record tick count, update `enc_counts_per_rev`.
2. **Wheel radius** — Drive straight 1 m, compare `/odom` X to ground truth.
3. **Chassis geometry** — Command `angular.z = 1.0` for 6.28 s; adjust
   `sum_of_robot_center_projection_on_X_Y_axis` until translation drift < 5 cm.
4. **Strafe test** — Command `linear.y = 0.1 m/s`; robot must move laterally
   with < 5 cm forward drift. This is the critical mecanum sanity check.

---

## IMU (ICM-20948)

The hardware interface reads accel + gyro from the Pico and fuses them into an
orientation quaternion (complementary filter, `hardware/include/mecanum_pico/imu_fusion.hpp`)
so the `imu_sensor_broadcaster` gets its required `orientation.x/y/z/w`
state interfaces on real hardware too.

**Keep the robot still for ~1 s after activation:** the first 100 standstill
samples calibrate the gyro zero-rate bias (logged once as
"Gyro bias calibrated…"). Samples taken while the robot accelerates are
skipped and merely extend the calibration window. Every controller
(re-)activation recalibrates.

---

## Migration from diffdrive_arduino

| Old | New |
|-----|-----|
| `diffdrive_arduino` | `mecanum_pico` |
| `DiffDriveArduinoHardware` | `MecanumPicoHardware` |
| `arduino_comms.hpp` | `pico_comms.hpp` |
| `Wheel left_wheel_, right_wheel_` | `Wheel wheel_fl_, wheel_fr_, wheel_rl_, wheel_rr_` |
| `diff_drive_controller` | `mecanum_drive_controller` |
| PID on host | PID on Pico |

---

## Sprint Status

| Sprint | Description | Status |
|--------|-------------|--------|
| 0 | Baseline fork, test scaffolding | ✅ Complete |
| 1 | 4-wheel data model | ✅ Complete |
| 2 | Serial protocol (4-value) | ✅ Complete |
| 3 | Full integration + URDF | ✅ Complete |
| 4 | Pico firmware | ✅ Complete |
| 5 | Float velocity protocol (optional) | ⏳ Future |
| 6 | Gazebo mock_hardware + CI launch test | ⏳ Scaffolded |
| 7 | Physical calibration + HIL validation | ⏳ Scaffolded |
