# gubot_navigation

SLAM-Kartierung, Karten-Verwaltung und der komplette **Nav2-Stack**
(Lokalisierung + autonome Navigation) für `gubot_one`. Läuft identisch auf
echter Hardware und in der Gazebo-Simulation — nur `use_sim_time` und die
Sensorquelle unterscheiden sich.

## Inhalt

```
launch/nav2.launch.py           # Haupt-Launch: Lokalisierung (AMCL ODER SLAM) + Navigation
launch/localization.launch.py   # map_server + AMCL + Lifecycle Manager
launch/navigation.launch.py     # Nav2-Serverkette (Controller/Planner/Behaviors/BT/…)
launch/slam.launch.py           # slam_toolbox (Online-Mapping, liefert map->odom)
launch/map_saver.launch.py      # map_saver_server (Karte per Service speichern)
launch/record_scan.launch.py    # rosbag2-Aufnahme von /scan + TF fuer Offline-SLAM
config/nav2_params.yaml         # Nav2-Parameter (Mecanum/omnidirektional, RPLidar A1)
config/slam_toolbox_params.yaml # slam_toolbox-Parameter
maps/test_area.{yaml,pgm}       # Gespeicherte Standard-Karte
scans/                          # rosbag2-Aufnahmen (record_scan)
```

## Was ist AMCL?

**AMCL = Adaptive Monte Carlo Localization** (`nav2_amcl`) — der
Lokalisierungs-Algorithmus, der die Roboterpose auf einer **bereits
gespeicherten Karte** schätzt:

- Er hält eine Wolke aus **Partikeln** (hier 500–2000), von denen jedes
  eine Pose-Hypothese "der Roboter könnte hier stehen" ist.
- Bei jeder Bewegung werden die Partikel gemäß Odometrie + Rauschmodell
  verschoben (hier `OmniMotionModel`, weil Mecanum auch seitwärts fährt).
- Bei jedem Lidar-Scan wird jedes Partikel danach gewichtet, wie gut der
  Scan von seiner Pose aus zur Karte passen würde; unwahrscheinliche
  Partikel sterben aus, gute werden vervielfältigt (Resampling).
- "Adaptive": die Partikelanzahl passt sich der Unsicherheit an — viele
  Partikel, wenn die Pose unklar ist, wenige, wenn sie konvergiert ist.

AMCL publiziert die **`map -> odom`-Transformation** — die Korrektur des
Odometrie-Drifts. Die Kette ist: `map ->(AMCL) odom ->(EKF) base_link`.

**AMCL vs. SLAM:** AMCL braucht eine fertige Karte und lokalisiert nur
darauf. `slam_toolbox` baut die Karte gleichzeitig neu auf (und liefert
dasselbe `map->odom`). Deshalb ist in `nav2.launch.py` genau **eines von
beiden** aktiv: `slam:=false` → AMCL + Karte, `slam:=true` → slam_toolbox.

> **Neu hier?** Schritt-für-Schritt-Workflow (Karte erstellen +
> navigieren, Sim): [`docs/sim_mapping_workflow.md`](../../docs/sim_mapping_workflow.md)

## Voraussetzung (immer)

Basis-Bringup läuft — Controller, EKF (`odom->base_link`), Lidar (`/scan`):

```bash
# Echte Hardware:
ros2 launch gubot_bringup launch_all_real.launch.py launch_lidar:=true

# Simulation (Gazebo Fortress, Lidar + Kamera in der Welt):
ros2 launch gubot_gazebo simulation.launch.py
```

## `nav2.launch.py` (Haupt-Einstieg)

Startet Lokalisierung (AMCL **oder** slam_toolbox) **plus** die
Nav2-Serverkette. Nav2 fährt über `/cmd_vel_nav` (twist_mux Priorität 10).

| Argument | Standard | Bedeutung |
|---|---|---|
| `slam` | `false` | `false`: map_server + AMCL gegen gespeicherte Karte. `true`: slam_toolbox (Online-Mapping). |
| `map` | `maps/test_area.yaml` | Karten-YAML für AMCL (nur bei `slam:=false`). |
| `params_file` | `config/nav2_params.yaml` | Nav2-Parameterdatei. |
| `use_sim_time` | `false` | `true` in der Gazebo-Simulation. |

```bash
# Echte Hardware, gespeicherte Karte (AMCL):
ros2 launch gubot_navigation nav2.launch.py

# Echte Hardware, ohne Karte (Online-SLAM):
ros2 launch gubot_navigation nav2.launch.py slam:=true

# Andere Karte:
ros2 launch gubot_navigation nav2.launch.py map:=/pfad/zu/karte.yaml

# Simulation:
ros2 launch gubot_navigation nav2.launch.py use_sim_time:=true slam:=true
```

Ziel senden: in RViz „Nav2 Goal" setzen oder

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.5}, orientation: {w: 1.0}}}}"
```

## `localization.launch.py` (map_server + AMCL separat)

| Argument | Standard | Bedeutung |
|---|---|---|
| `map` | `maps/test_area.yaml` | Pfad zur Karten-YAML (nav2_map_server). |
| `params_file` | `config/nav2_params.yaml` | Nav2-Parameterdatei. |
| `use_sim_time` | `false` | Sim-Time aktivieren. |

## `navigation.launch.py` (Nav2-Serverkette separat)

Controller, Planner, Smoother, Behaviors, BT Navigator, Waypoint Follower
+ Lifecycle Manager. Braucht `map->odom` von AMCL **oder** slam_toolbox.

| Argument | Standard | Bedeutung |
|---|---|---|
| `params_file` | `config/nav2_params.yaml` | Nav2-Parameterdatei. |
| `use_sim_time` | `false` | Sim-Time aktivieren. |

## `slam.launch.py` (slam_toolbox separat)

| Argument | Standard | Bedeutung |
|---|---|---|
| `params_file` | `config/slam_toolbox_params.yaml` | slam_toolbox-Parameterdatei. |
| `use_sim_time` | `false` | Sim-Time aktivieren. |

## `map_saver.launch.py` (Karte speichern)

| Argument | Standard | Bedeutung |
|---|---|---|
| `use_sim_time` | `false` | Sim-Time aktivieren. |
| `save_map_timeout` | `5.0` | Timeout (s) pro save_map-Anfrage. |

```bash
ros2 launch gubot_navigation map_saver.launch.py
ros2 run nav2_map_server map_saver_cli -f src/gubot_navigation/maps/meine_karte
```

## `record_scan.launch.py` (Scan-Aufnahme für Offline-SLAM)

| Argument | Standard | Bedeutung |
|---|---|---|
| `scans_dir` | `<pkg-src>/scans` | Zielverzeichnis für rosbag2-Aufnahmen. |
| `bag_name` | `scan_recording` | Name der Aufnahme (Unterordner unter `scans_dir`). |

## Nav2-Parameter — die Gubot-spezifischen Abweichungen

`config/nav2_params.yaml` basiert auf den Humble-Defaults, geändert:

- `robot_model_type: nav2_amcl::OmniMotionModel` — Mecanum fährt seitwärts.
- DWB mit `min/max_vel_y ±0.4` und `vy_samples: 10` — Quergeschwindigkeit
  wird aktiv geplant.
- `min_y_velocity_threshold: 0.001` — Default 0.5 würde vy wegfiltern.
- `base_frame_id: base_link` (kein `base_footprint`), `odom->base_link`
  kommt vom EKF (`/odometry/filtered`).
- Lidar `/scan`, max. 12 m (RPLidar A1).
- `cmd_vel` wird im Launch auf `/cmd_vel_nav` remappt (twist_mux-Eingang).

## Nützliche Introspektions-Befehle

```bash
ros2 lifecycle get /amcl                  # active?
ros2 topic hz /scan
ros2 topic echo /cmd_vel_nav
ros2 action list | grep navigate
ros2 run tf2_tools view_frames            # map->odom->base_link prüfen
```
