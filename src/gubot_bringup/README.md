# gubot_bringup

Bringup für den **echten** `gubot_one`-Roboter (Raspberry Pi): bindet die
Controller-Kette (`gubot_controller`), EKF (`gubot_localization`),
Joystick-Teleop, optional RPLidar, USB-Kamera und Gesichtserkennung
(`face_tracker`) ein. Das Gazebo-Pendant ist
[`gubot_gazebo`](../gubot_gazebo/README.md).

## Inhalt

```
launch/launch_all_real.launch.py   # Haupt-Launch für echte Hardware
launch/joystick.launch.py          # joy_node + teleop_node + nerf_joy
launch/camera.launch.py            # v4l2_camera (Standard-Kameratreiber)
launch/real_camera.launch.py       # usb_cam (Alternative, MJPEG-optimiert)
launch/rplidar.launch.py           # RPLidar-Treiber
launch/sentry.launch.py            # Sentry-Modus: Nav2 + Face Tracking + Nerf-Feuer
config/joystick.yaml               # joy_node + teleop_node Parameter
```

## Schnellstart (auf dem Roboter/Raspberry Pi)

```bash
cd ~/projects/my_new_robot_9e34131   # Workspace-Root
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 launch gubot_bringup launch_all_real.launch.py
```

Startet: Controller-Kette (RSP, `ros2_control_node`, Mecanum-Antrieb, IMU,
Joint States, Nerf-Kette), Twist Mux, EKF, Joystick-Teleop
(`teleop_node` + `nerf_joy` — **ohne** `joy_node`, siehe unten).

> Bequemer über `gubot_utils/scripts/start_robot.sh` starten — siehe
> [`gubot_utils/README.md`](../gubot_utils/README.md), das setzt zusätzlich
> die DDS-Config und bietet Kurz-Flags (`--face`, `--armed`, …).

## Launch-Argumente (`launch_all_real.launch.py`)

| Argument | Standard | Bedeutung |
|---|---|---|
| `launch_lidar` | `false` | RPLidar starten (kein Lidar standardmäßig verbaut). |
| `launch_camera` | `false` | Kamera starten (aktuell defekt/optional). |
| `camera_type` | `v4l2` | `v4l2` (→ `camera.launch.py`) oder `usb_cam` (→ `real_camera.launch.py`, MJPEG). |
| `auto_arm` | `false` | Nerf-System beim Start automatisch scharfschalten. **Vorsicht.** |
| `launch_face_tracker` | `false` | Gesichtserkennung starten (braucht `launch_camera:=true`, Start verzögert um 12 s). |
| `target_person` | `""` (leer) | Zielperson für Gesichtsverfolgung (leer = beliebige Person). |
| `allow_search` | `false` | Roboter darf rotieren, um ein Gesicht zu suchen. |

Beispiele:

```bash
# Mit RPLidar
ros2 launch gubot_bringup launch_all_real.launch.py launch_lidar:=true

# Mit Kamera (usb_cam/MJPEG) + Gesichtsverfolgung einer bestimmten Person
ros2 launch gubot_bringup launch_all_real.launch.py \
  launch_camera:=true camera_type:=usb_cam \
  launch_face_tracker:=true target_person:=max allow_search:=true

# Nerf-System sofort scharf (nur wenn du weißt was du tust!)
ros2 launch gubot_bringup launch_all_real.launch.py auto_arm:=true
```

## Sentry-Modus (`sentry.launch.py`)

Startet die komplette Sentry-Kette **auf einem bereits laufenden
Basis-Bringup**: Nav2 (autonomes Fahren) + Face Tracker (Verfolgung) +
`fire_at_face` (Nerf-Feuer bei zentriertem, nahem Ziel).

Prioritäten (twist_mux): Joystick 100 > Tracker 20 > Nav2 10 — der
Tracker übersteuert Nav2, der Joystick übersteuert alles.

Voraussetzung (echte Hardware):

```bash
ros2 launch gubot_bringup launch_all_real.launch.py \
    launch_lidar:=true launch_camera:=true use_nerf_hardware:=true
```

| Argument | Standard | Bedeutung |
|---|---|---|
| `slam` | `false` | `false`: AMCL gegen gespeicherte Karte. `true`: slam_toolbox (Online-Mapping). |
| `map` | `gubot_navigation/maps/test_area.yaml` | Karten-YAML für AMCL (nur `slam:=false`). |
| `use_sim_time` | `false` | `true` in der Gazebo-Simulation. |
| `target_person` | `""` (leer) | Zu verfolgende/beschießende Person (leer = beliebiges Gesicht). |
| `image_topic` | `/camera/image_raw` | Eingangs-Bildtopic für `detect_face`. |
| `launch_face_tracker` | `true` | Face-Tracking + Feuer-Kette starten (`false` = nur Nav2). |

```bash
ros2 launch gubot_bringup sentry.launch.py
ros2 launch gubot_bringup sentry.launch.py slam:=true
ros2 launch gubot_bringup sentry.launch.py target_person:=Marco

# In der Simulation (nach gubot_gazebo/simulation.launch.py):
ros2 launch gubot_bringup sentry.launch.py use_sim_time:=true slam:=true
```

Alle Nav2-Details (Argumente, Parameter, AMCL-Erklärung) stehen in
[`gubot_navigation/README.md`](../gubot_navigation/README.md).

## Joystick separat (`joystick.launch.py`)

| Argument | Standard | Bedeutung |
|---|---|---|
| `use_sim_time` | `false` | |
| `launch_joy_node` | `true` | `false`, wenn `joy_node` auf einem anderen Rechner läuft (z. B. Fernsteuerung über Tailscale/DDS — Standardfall in `launch_all_real.launch.py`). |
| `tilt_command_topic` | `/tilt_controller/commands` | Ziel-Topic für Tilt-Kommandos (umbiegbar für Sim-Adapter). |

```bash
# Auf dem Remote-PC mit angeschlossenem Gamepad (joy_node läuft dort):
ros2 run joy joy_node

# Auf dem Roboter selbst testen (Gamepad direkt am Pi):
ros2 launch gubot_bringup joystick.launch.py launch_joy_node:=true
```

Button-Mapping (Xbox-Controller) steht im Docstring von
`gubot_utils/scripts/teleop__nerf_joystick.py`.

## Kamera separat

```bash
# v4l2_camera (Standard, YUYV, 320x240 @10fps) -> /camera/image_raw
ros2 launch gubot_bringup camera.launch.py

# usb_cam (MJPEG, 320x240 @10fps) -> /camera/image_raw
ros2 launch gubot_bringup real_camera.launch.py
ros2 launch gubot_bringup real_camera.launch.py camera_namespace:=my_camera
```

## RPLidar separat

```bash
ros2 launch gubot_bringup rplidar.launch.py
```

Serial-Port ist hart kodiert
(`/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-port0`)
— bei anderem Lidar-Kabel/Port in `launch/rplidar.launch.py` anpassen.

## Nützliche Introspektions-Befehle

```bash
ros2 topic echo /joy
ros2 topic echo /cmd_vel_joy
v4l2-ctl --list-devices          # Kamera-Device-Pfad prüfen
ls -l /dev/serial/by-path/       # Lidar-Port prüfen
```
