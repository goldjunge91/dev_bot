# gubot_gazebo

Simulations-Bringup für `gubot_one` in Ignition/Gazebo Fortress (`gz sim`):
startet die Welt, spawnt den Roboter, bindet die Sensor-/Clock-Bridges
(`ros_gz_bridge`) ein und startet darüber `gubot_controller` (Controller)
und `gubot_localization` (EKF). Das ist der **Haupt-Einstiegspunkt für die
Simulation**.

## Inhalt

```
launch/simulation.launch.py   # Haupt-Launch: gz sim + Clock-Bridge + spawn_robot + RViz
launch/spawn_robot.launch.py  # Spawn-Entity + Sensor-Bridge + controller.launch.py + ekf.launch.py
worlds/obstacles.world        # Standard-Welt (Hindernisse: construction_barrel/cone)
worlds/empty.world            # Leere Welt
config/gz_bridge.yaml         # Globale Bridge (nur /clock)
config/gubot_bridge.yaml      # Per-Robot Bridge (scan, camera, imu/data_raw, cmd_vel)
```

## Schnellstart

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to gubot_gazebo
source install/setup.bash

ros2 launch gubot_gazebo simulation.launch.py
```

Das startet: Ignition Gazebo (GUI) + `obstacles.world` + `gubot_one`
(Spawn bei `x=0 y=0 z=0.05`) + Controller-Kette + EKF + RViz.

> **Hinweis (Memory):** Immer mit GUI starten (`rviz`-Argument nicht auf
> `false` setzen) — keine Headless-Simulation. Vor dem Start prüfen, ob
> bereits eine Instanz läuft: `ps aux | grep -E "ign gazebo|rviz2"`.

## Launch-Argumente (`simulation.launch.py`)

| Argument | Standard | Bedeutung |
|---|---|---|
| `world` | `worlds/obstacles.world` | Pfad zur `.world`-Datei. |
| `use_nerf_hardware` | `true` | An `spawn_robot.launch.py` → `controller.launch.py` durchgereicht. |
| `use_camera` | `true` | Gazebo-Kamerasensor an/aus (RTF-Boost unter WSL2/llvmpipe bei `false`). |
| `rviz` | `True` | RViz parallel starten (`True`/`true`/`False`/`false`). |

Beispiele:

```bash
# Andere Welt
ros2 launch gubot_gazebo simulation.launch.py world:=src/gubot_gazebo/worlds/empty.world

# Schnellere Sim unter WSL2 (keine Kamera-Render-Last)
ros2 launch gubot_gazebo simulation.launch.py use_camera:=false

# Ohne Nerf-Launcher-Controller
ros2 launch gubot_gazebo simulation.launch.py use_nerf_hardware:=false

# Ohne RViz (nur Gazebo)
ros2 launch gubot_gazebo simulation.launch.py rviz:=false
```

## Launch-Argumente (`spawn_robot.launch.py`)

Normalerweise nicht direkt aufgerufen (wird von `simulation.launch.py`
eingebunden), aber für Mehrfach-Spawns oder eine andere Startpose nützlich:

| Argument | Standard | Bedeutung |
|---|---|---|
| `x` / `y` / `z` | `0.0` / `0.0` / `0.05` | Start-Position. |
| `roll` / `pitch` / `yaw` | `0.0` / `0.0` / `0.0` | Start-Orientierung (rad). |
| `use_sim_time` | `true` | An `controller.launch.py`/EKF durchgereicht. |
| `use_nerf_hardware` | `false` | **Achtung:** eigener Default hier `false`, wird aber von `simulation.launch.py` immer explizit auf `true` gesetzt. |
| `use_camera` | `true` | s.o. |

```bash
# Roboter an anderer Startposition spawnen (z. B. zweite Instanz in derselben Welt)
ros2 launch gubot_gazebo spawn_robot.launch.py x:=2.0 y:=1.0 yaw:=1.57
```

> **Schritt-für-Schritt-Anleitung** (Mapping + Navigation in der Sim,
> für neue Nutzer): [`docs/sim_mapping_workflow.md`](../../docs/sim_mapping_workflow.md)

## Nav2 / Sentry in der Simulation

Die Simulation liefert alles, was Nav2 braucht (`/scan`, Kamera, EKF,
twist_mux). In einem zweiten Terminal:

```bash
# Nur Navigation (Online-SLAM, da die Sim-Welt keine gespeicherte Karte hat):
ros2 launch gubot_navigation nav2.launch.py use_sim_time:=true slam:=true

# Komplette Sentry-Kette (Nav2 + Face Tracking + Nerf-Feuer):
ros2 launch gubot_bringup sentry.launch.py use_sim_time:=true slam:=true
```

Details: [`gubot_navigation/README.md`](../gubot_navigation/README.md).

## Bekannte Stolpersteine

```bash
# "Entity already exists" / Karteileichen nach abgebrochenem Lauf:
pkill -9 -f "ign gazebo" ; pkill -9 rviz2
ps aux | grep -E "(ign gazebo|launch)" | grep -v grep
ros2 daemon stop

# Meshes werden nicht geladen ("Unable to find file with URI [model://...]"):
# → Mesh-Pfade in URDF/Xacro MÜSSEN file://$(find <pkg>)/... sein, nicht
#   package://... (Ignition Fortress löst package:// zu model:// auf und
#   findet es dann nicht). Siehe gubot_description/urdf/gubot_one_geometry.xacro.
```

## Nützliche Introspektions-Befehle

```bash
ros2 topic list
ros2 topic hz /scan
ros2 service call /world/<world_name>/control ros_gz_interfaces/srv/ControlWorld "{}"
gz topic -l          # Ignition-native Topics (vor der Bridge)
```
