# gubot_controller

ros2_control-Bringup für `gubot_one`: startet `robot_state_publisher`
(über `gubot_description`), `twist_mux`, den `controller_manager` (nur bei
echter Hardware — in der Simulation übernimmt `gz_ros2_control` das) und
alle Controller-Spawner (Mecanum-Antrieb, IMU, Joint States, Nerf-Kette).

Wird eingebunden von `gubot_gazebo/launch/spawn_robot.launch.py` (Sim) bzw.
`gubot_bringup/launch/launch_all_real.launch.py` (echte Hardware) — siehe
[`gubot_gazebo/README.md`](../gubot_gazebo/README.md) und
[`gubot_bringup/README.md`](../gubot_bringup/README.md). Kann aber auch
eigenständig getestet werden (z. B. für Controller-Debugging ohne Gazebo).

## Inhalt

```
launch/controller.launch.py     # RSP + twist_mux + controller_manager + Spawner
config/controllers.yaml         # controller_manager: Controller-Typen + Parameter
config/twist_mux.yaml           # Prioritäten für cmd_vel-Quellen
```

## Schnellstart

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to gubot_controller
source install/setup.bash

# Nur die Controller-Kette (setzt echte Hardware voraus, siehe use_sim_time)
ros2 launch gubot_controller controller.launch.py
```

> Für eine reine Simulation nicht dieses Launch-File direkt starten,
> sondern `ros2 launch gubot_gazebo simulation.launch.py` — das bindet
> `controller.launch.py` bereits mit `use_sim_time:=true` ein.

## Launch-Argumente (`controller.launch.py`)

| Argument | Standard | Bedeutung |
|---|---|---|
| `use_sim_time` | `false` | `true`: kein eigener `ros2_control_node` (der läuft in Gazebo via `gz_ros2_control`), ROS-Zeit von `/clock`. `false`: startet `ros2_control_node` selbst (echte Hardware). |
| `use_ros2_control` | `true` | An `load_urdf.launch.py` durchgereicht — deaktiviert den `<ros2_control>`-Block im URDF. |
| `use_nerf_hardware` | `true` | Startet zusätzlich `tilt_controller`, `shooter_controller`, `arming_controller` + `nerf_control_node` (verzögert nach dem Basis-Spawner, um DDS-Discovery-Lastspitzen zu vermeiden). |
| `use_camera` | `true` | An `load_urdf.launch.py` durchgereicht. |
| `auto_arm` | `false` | Startparameter des `nerf_control_node` — Nerf-System beim Start automatisch scharfschalten. **Vorsicht auf echter Hardware.** |

Beispiele:

```bash
# Nur Basis-Antrieb, kein Nerf-Launcher
ros2 launch gubot_controller controller.launch.py use_nerf_hardware:=false

# Echte Hardware, Nerf-System sofort scharf (nur wenn du weißt was du tust!)
ros2 launch gubot_controller controller.launch.py auto_arm:=true
```

## Twist Mux (`twist_mux.yaml`)

Priorisiert `cmd_vel`-Quellen (höher gewinnt), Output geht per Remap auf
`/cmd_vel`:

| Quelltopic | Priorität | Timeout |
|---|---|---|
| `cmd_vel_joy` (Joystick) | 100 | 0.5 s |
| `cmd_vel_tracker` (Gesichtsverfolgung) | 20 | 0.5 s |
| `cmd_vel_nav` (Navigation) | 10 | 0.5 s |

```bash
# Manuell auf eine Quelle publizieren (z. B. Navigation simulieren):
ros2 topic pub -1 /cmd_vel_nav geometry_msgs/msg/Twist "{linear: {x: 0.1}}"
```

## Geladene Controller (`controllers.yaml`)

| Controller | Typ | Zweck |
|---|---|---|
| `mecanum_drive_controller` | `mecanum_drive_controller/MecanumDriveController` | `cmd_vel` → 4× Radgeschwindigkeit, publiziert Odometrie. |
| `imu_broadcaster` | `imu_sensor_broadcaster/IMUSensorBroadcaster` | Publiziert `imu/data`. |
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | Publiziert `/joint_states`. |
| `tilt_controller` | `position_controllers/JointGroupPositionController` | Nerf-Launcher Neigung. |
| `shooter_controller` | `velocity_controllers/JointGroupVelocityController` | Nerf-Flywheels. |
| `arming_controller` | `forward_command_controller/ForwardCommandController` | Nerf-Sicherung (scharf/entschärft). |

`controller_manager.update_rate: 100` Hz (`ros__parameters` unter `/**:`,
damit es mit und ohne Namespace funktioniert).

**Wichtiger Kinematik-Parameter:** `mecanum_drive_controller.wheel_radius`
(aktuell `0.05` m) und `wheel_separation_x/y` (`0.226`/`0.297` m) müssen zu
den Maßen in
[`gubot_description/config/robot_dimensions.yaml`](../gubot_description/config/robot_dimensions.yaml)
passen (`wheel_radius`, `2 × wheel_offset_x/y`) — sonst driftet die
Odometrie. Wird durch `gubot_controller/tests/test_controller_yaml.py` und
`gubot_description/tests/test_urdf_variants.py` (Drift-Wache) abgesichert.

## Nützliche Introspektions-Befehle

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic echo /odometry/wheels
ros2 topic pub -1 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"
```

## Tests

```bash
colcon test --packages-select gubot_controller
colcon test-result --verbose
# oder direkt:
python3 -m pytest src/gubot_controller/tests/ -q
```
