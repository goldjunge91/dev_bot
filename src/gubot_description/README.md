# gubot_description

URDF/Xacro-Beschreibung von `gubot_one`, Meshes, Materialien, Sensor-Xacros
(Kamera, IMU, Nerf-Launcher-Anbindung) und RViz-Configs. Startet den
`robot_state_publisher`, der `robot_description` aus der Xacro-Datei
generiert und die TF-Kette publiziert.

Wird normalerweise **nicht direkt** gestartet, sondern von
`gubot_controller/launch/controller.launch.py` eingebunden — siehe
[`gubot_controller/README.md`](../gubot_controller/README.md). Für einen
isolierten Blick auf das Modell (nur URDF + RViz, keine Controller/Sim)
reicht dieses Paket allein.

## Inhalt

```
config/
└── robot_dimensions.yaml              # Einzige Quelle der Wahrheit: Chassis-/Rad-Maße
urdf/
├── gubot_one_main.urdf.xacro          # Einstiegspunkt (bindet alles zusammen)
├── properties.xacro                   # Alle xacro-Properties + Materialien (lädt robot_dimensions.yaml)
├── gubot_one_geometry.xacro           # Reine Geometrie: Chassis, Räder, IMU (keine Gazebo-Tags)
├── mecanum_wheel.xacro                # Rad-Makro (Joint + Link + Inertial), 4x instanziiert
├── gazebo_sim.xacro                   # Sim-only: IMU-Sensor, Mecanum-Reibung (fdir1), Gazebo-Materialien — nur bei sim_mode:=true
├── inertial_macros.xacro              # inertial_sphere/box/cylinder
├── ros2_control_common.xacro          # Gemeinsame ros2_control-Makros (Rad-Joint, IMU-Sensor)
├── ros2_control_gazebo_ign_fortress.xacro   # sim_mode:=true (GubotIgnitionSystem)
├── ros2_control_hardware.xacro        # sim_mode:=false (RealRobot, mecanum_pico; Params als xacro-Args)
├── sensor_camera.xacro / sensor_lidar.xacro
├── sensor_depth_camera.xacro          # Optionale Tiefenkamera (use_depth_camera:=true, Standard aus)
├── visual_face.xacro                  # Gesichts-Display-Link
└── nerf_launch_system.xacro           # bindet src/nerf_launch_system ein (use_nerf_hardware:=true)
meshes/bases/waffle_pi_base.stl        # Chassis-Visual
meshes/wheels/mecanum_a.dae            # rechtes Mecanum-Rad (fr, rr)
meshes/wheels/mecanum_b.dae            # linkes Mecanum-Rad (fl, rl)
rviz/main.rviz
launch/load_urdf.launch.py
tests/test_urdf_geometry.py            # Rad-Symmetrie
tests/test_urdf_variants.py            # Varianten-Matrix, stabile Namen, fdir1, check_urdf, Drift-Wache controllers.yaml
```

## Schnellstart

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to gubot_description
source install/setup.bash

# Nur robot_state_publisher (ohne Controller/Simulation)
ros2 launch gubot_description load_urdf.launch.py
```

### Modell in RViz ansehen (ohne Sim/Hardware)

```bash
ros2 launch gubot_description load_urdf.launch.py use_ros2_control:=false
# in einem zweiten Terminal:
rviz2 -d install/gubot_description/share/gubot_description/rviz/main.rviz
```

### Nur URDF prüfen (xacro-Expansion + Validierung, kein Node-Start)

```bash
xacro src/gubot_description/urdf/gubot_one_main.urdf.xacro use_ros2_control:=false > /tmp/gubot_one.urdf
check_urdf /tmp/gubot_one.urdf
```

## Launch-Argumente (`load_urdf.launch.py`)

| Argument | Standard | Bedeutung |
|---|---|---|
| `use_sim_time` | `false` | `true` = ROS-Zeit von `/clock` (Simulation) statt Systemzeit. |
| `use_ros2_control` | `true` | Bindet den ros2_control-`<ros2_control>`-Block ins URDF ein. `false` = reines Anzeige-Modell ohne Hardware-Interfaces. |
| `sim_mode` | `false` | Wählt zwischen `ros2_control_gazebo_ign_fortress.xacro` (`true`) und `ros2_control_hardware.xacro` (`false`). Wird i.d.R. automatisch mit `use_sim_time` synchron gesetzt (siehe `gubot_controller`/`gubot_gazebo`). |
| `use_nerf_hardware` | `true` | Bindet `nerf_launch_system.xacro` (Launcher-Links, -Joints, -ros2_control-Interfaces) ein. |
| `use_camera` | `true` | Bindet den Gazebo-Kamerasensor ein. `false` entfernt nur den Render-Sensor (spart Rechenzeit, z. B. unter WSL2) — Kamera-Link/TF bleiben erhalten. |
| `use_depth_camera` | `false` | Bindet die optionale Tiefenkamera (`depth_camera_*`-Frames, gz-Fortress-`depth_camera`-Sensor, Topic `camera/depth`) ein. |
| `controller_config` | `gubot_controller/config/controllers.yaml` | Pfad zu `controllers.yaml`, wird in den `<ros2_control>`-Xacro-Block injiziert (Pluginlib-Namen/Update-Rate). |
| `drive_device` | Pico by-id-Pfad | Serielles Gerät der Antriebs-Hardware (`mecanum_pico`), nur `sim_mode:=false`. |
| `nerf_port` | Leonardo by-id-Pfad | Serielles Gerät des Nerf-Launchers, nur `sim_mode:=false` + `use_nerf_hardware:=true`. |

Weitere Hardware-Parameter (`drive_baud_rate`, `drive_loop_rate`,
`drive_timeout_ms`, `enc_counts_per_rev`, `nerf_tilt_min/max`) sind als
xacro-Args in `ros2_control_hardware.xacro` deklariert und können direkt an
`xacro` übergeben werden (Defaults = bisherige Festwerte).

Beispiel mit allen Optionen:

```bash
ros2 launch gubot_description load_urdf.launch.py \
  use_sim_time:=true \
  use_ros2_control:=true \
  sim_mode:=true \
  use_nerf_hardware:=true \
  use_camera:=false \
  use_depth_camera:=true
```

## Roboter-Maße ändern (`config/robot_dimensions.yaml`)

Chassis- und Radmaße liegen zentral in `config/robot_dimensions.yaml`
(von `urdf/properties.xacro` per `xacro.load_yaml` geladen — **nicht** mehr
in den xacro-Dateien selbst):

| Schlüssel | Wert | Bedeutung |
|---|---|---|
| `chassis_length/width/height` | 0.335 / 0.265 / 0.138 m | Chassis-Box (Collision) + Skalierungsbasis für `waffle_pi_base.stl` (Visual). |
| `wheel_radius` / `wheel_thickness` | 0.05 / 0.05 m | Reale Maße des 100mm-Aluminum-Mecanum-Rads (`mecanum_a/b.dae`). Muss synchron zu `gubot_controller/config/controllers.yaml → mecanum_drive_controller.wheel_radius` gehalten werden, sonst driftet die Odometrie. |
| `wheel_offset_x` / `wheel_offset_y` | 0.113 / 0.1485 m | Radstand halbe Länge/Breite. Muss synchron zu `wheel_separation_x/y` in `controllers.yaml` sein (`separation = 2 × offset`). |

Die Synchronität mit `controllers.yaml` wird automatisch geprüft:
`tests/test_urdf_variants.py::test_wheel_geometry_consistent_with_controllers_yaml`
schlägt fehl, wenn die Werte auseinanderlaufen. Weitere Stellschrauben
(Joint-Limits, Reibungs-µ/slip, IMU-Rate) sind benannte Properties in
`urdf/properties.xacro`.

## Abhängigkeiten

`xacro`, `robot_state_publisher`, `joint_state_publisher_gui` (nur für
manuelles Gelenk-Testen ohne Controller).
