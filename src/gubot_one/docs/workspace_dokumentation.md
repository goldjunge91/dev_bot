# Workspace-Dokumentation: gubot_one

> **Automatisch generiert** aus dem Quellcode-Analyse-Durchlauf.  
> Paket: `gubot_one` | ROS2 (Humble/Iron) | Stand: 2025

---

## Inhaltsverzeichnis

1. [Überblick & Architektur](#überblick--architektur)
2. [description/ – Roboterbeschreibung (URDF/Xacro)](#description--roboterbeschreibung-urdfxacro)
3. [launch/ – Launch-Dateien](#launch--launch-dateien)
4. [Abhängigkeitsmatrix](#abhängigkeitsmatrix)

---

## Überblick & Architektur

Der `gubot_one` ist ein differenzialgetriebener Roboter mit:
- **Antrieb**: 2 angetriebene Räder (links/rechts) + 1 Stützrad
- **Sensorik**: IMU, USB-Kamera (optional), RPLidar (optional)
- **Sonderausstattung**: Nerf-Launcher (Arduino/Pico gesteuert)
- **Steuerung**: ros2_control mit `diffdrive_arduino`-Plugin (Hardware) / Ignition/Gazebo-Plugin (Simulation)

```
robot.urdf.xacro
  ├── robot_core.xacro         (Chassis, Räder, IMU)
  ├── inertial_macros.xacro    (Trägheitsmoment-Helfer)
  ├── ros2_control.xacro       (Ignition Sim + echte Hardware)
  │   ODER
  │   gz_classic_ros2_control.xacro  (Gazebo Classic)
  │   ODER
  │   gazebo_control.xacro     (Legacy Diff-Drive Plugin)
  ├── camera.xacro             (RGB-Kamera)
  ├── face.xacro               (Gesichts-Visualisierung)
  └── nerf_launcher.xacro      (Nerf-Launcher mount)
```

---

## description/ – Roboterbeschreibung (URDF/Xacro)

---

### `robot.urdf.xacro`
**Pfad:** `description/robot.urdf.xacro`

**Was es ist:** Die Haupt-URDF-Einstiegsdatei. Sie wird von nahezu allen Launch-Dateien über `xacro` verarbeitet
und steuert per Argumente, welche Subsysteme eingebunden werden.

**Argumente:**

| Argument | Standard | Bedeutung |
|---|---|---|
| `use_ros2_control` | `true` | Aktiviert ros2_control statt Legacy-Plugin |
| `sim_mode` | `false` | Schaltet zwischen Hardware und Simulation |
| `integrated_mode` | `true` | Nerf-Launcher + Basis zusammen starten |
| `use_nerf_hardware` | `true` | Nerf-Hardware-Interface einbinden |
| `nerf_port` | `/dev/serial/...Leonardo` | Serieller Port des Arduino |
| `use_gazebo_classic` | `false` | Gazebo Classic statt Ignition Gazebo |

**Include-Logik:**
```
use_ros2_control=true + use_gazebo_classic=true  → gz_classic_ros2_control.xacro
use_ros2_control=true + use_gazebo_classic=false → ros2_control.xacro
use_ros2_control=false                           → gazebo_control.xacro (Legacy)
```

**Immer eingebunden:** `robot_core.xacro`, `camera.xacro`, `face.xacro`, `nerf_launcher.xacro`
**Auskommentiert:** `lidar.xacro`, `depth_camera.xacro`

**Verwendet von:**
- `rsp.launch.py` (via `xacro`-Command zur Laufzeit)
- `launch_robot.launch.py` (direkt als `robot_description` für Controller Manager)
- `launch_sim.launch.py`
- `gz_classic_launch_sim.launch.py`

---

### `robot_core.xacro`
**Pfad:** `description/robot_core.xacro`

**Was es ist:** Definiert die komplette physische Struktur des Roboters: Chassis, Antriebsräder, Stützrad und IMU.
Enthält alle Maße, Massen, Materialien und Gazebo-Sensor-Definitionen.

**Eingebundene Dateien:** `inertial_macros.xacro`

**Definierte Links & Joints:**

| Link | Typ | Beschreibung |
|---|---|---|
| `base_link` | leer | Referenzpunkt für alle anderen Links |
| `base_footprint` | leer | Bodenprojekt (für Navigation) |
| `chassis` | Box 335×265×138 mm | Orangefarbener Hauptkörper |
| `imu_link` | Box 20×20×20 mm | IMU-Sensor, 5 cm über Chassis |
| `left_wheel` | Zylinder r=33mm | Linkes Antriebsrad |
| `right_wheel` | Zylinder r=33mm | Rechtes Antriebsrad |
| `caster_wheel` | Kugel r=10mm | Passives Stützrad vorne |

**IMU-Konfiguration:**
- Update-Rate: 50 Hz
- Gausssches Rauschen auf Winkelgeschwindigkeit und Beschleunigung
- Gazebo Classic: `libgazebo_ros_imu_sensor.so` → Topic `imu/data`
- Ignition: Topic `imu_sensor/imu_data`

**Verwendet von:** `robot.urdf.xacro`

---

### `inertial_macros.xacro`
**Pfad:** `description/inertial_macros.xacro`

**Was es ist:** Bibliothek mit drei Xacro-Makros zur Berechnung physikalisch korrekter Trägheitsmomente.

**Makros:**

| Makro | Formel | Verwendet für |
|---|---|---|
| `inertial_sphere` | I = (2/5)mr² | Caster Wheel |
| `inertial_box` | Standard Quader-Formel | Chassis, IMU |
| `inertial_cylinder` | Standard Zylinder-Formel | Antriebsräder |

**Verwendet von:** `robot_core.xacro`, `lidar.xacro`

---

### `ros2_control.xacro`
**Pfad:** `description/ros2_control.xacro`

**Was es ist:** ros2_control-Konfiguration für **Ignition Gazebo** und **echte Hardware**.
Definiert welche Controller-Plugins geladen werden und welche Joints sie steuern.

**Hardware-Modus (`sim_mode=false`):**
- Plugin: `diffdrive_arduino/DiffDriveArduinoHardware`
- Gerät: Raspberry Pi Pico via USB
- Baud-Rate: 115200, Loop-Rate: 30 Hz, Encoder: 3436 Counts/Umdrehung

**Nerf-Hardware (`use_nerf_hardware=true`):**
- Plugin: `nerf_launch_system/NerfSystem`
- Port: Arduino Leonardo
- Joints: `trigger_joint`, `dart_pusher_joint`, `flywheel_left_joint`, `flywheel_right_joint`, `system_arming_joint`

**Simulations-Modus (`sim_mode=true`):**
- Plugin: `ign_ros2_control/IgnitionSystem`
- Gazebo-Plugin: `ign_ros2_control-system` lädt `my_controllers.yaml` + `gaz_ros2_ctl_use_sim.yaml`

**Verwendet von:** `robot.urdf.xacro` (wenn `use_ros2_control=true` und `use_gazebo_classic=false`)

---

### `gz_classic_ros2_control.xacro`
**Pfad:** `description/gz_classic_ros2_control.xacro`

**Was es ist:** Identisch zu `ros2_control.xacro`, aber für **Gazebo Classic** angepasst.

**Unterschied zu `ros2_control.xacro`:**

| Eigenschaft | `ros2_control.xacro` | `gz_classic_ros2_control.xacro` |
|---|---|---|
| Sim-Plugin | `ign_ros2_control/IgnitionSystem` | `gazebo_ros2_control/GazeboSystem` |
| Gazebo-Plugin-Datei | `ign_ros2_control-system` | `libgazebo_ros2_control.so` |

**Verwendet von:** `robot.urdf.xacro` (wenn `use_ros2_control=true` und `use_gazebo_classic=true`)

---

### `gazebo_control.xacro`
**Pfad:** `description/gazebo_control.xacro`

**Was es ist:** Legacy-Fallback. Nutzt `libgazebo_ros_diff_drive.so` **ohne** ros2_control.
Gazebo übernimmt direkt Odometrie und Steuerung.

**Parameter:** Radabstand 297 mm, Raddurchmesser 66 mm
**Publiziert:** Odometrie-Topic, TF `odom → base_link`, Rad-TF

**Verwendet von:** `robot.urdf.xacro` (wenn `use_ros2_control=false`)
**Hinweis:** In der aktuellen Konfiguration standardmäßig **nicht aktiv**.

---

### `camera.xacro`
**Pfad:** `description/camera.xacro`

**Was es ist:** Definiert den RGB-Kamera-Link. Vorne am Chassis montiert, leicht nach unten geneigt.

**Montage:** `xyz="0.276 0 0.181"`, Neigung 0.18 rad (~10°) nach unten

**Links:**
- `camera_link`: Visuelle Box + Halterungsstab
- `camera_link_optical`: Optischer Frame (REP-103-konform, rotiert -90° in X und Z)

**Sensor:** 640×480 RGB, FOV 1.089 rad, 10 Hz, Clip 5 cm–8 m
- Gazebo Classic: `libgazebo_ros_camera.so`
- Ignition: Topic `/camera/image_raw`

**Verwendet von:** `robot.urdf.xacro` (immer eingebunden)

---

### `lidar.xacro`
**Pfad:** `description/lidar.xacro`

**Was es ist:** Simulierter LIDAR-Sensor. Aktuell **auskommentiert** – echter RPLidar wird über `rplidar.launch.py` gestartet.

**Sensor:** 360°-Scan, 360 Samples, Range 0.3–12 m
- Gazebo Classic: `libgazebo_ros_ray_sensor.so`, Topic `/scan`
- Ignition: GPU-Lidar, Topic `scan`

**Verwendet von:** `robot.urdf.xacro` (auskommentiert – nicht aktiv)

---

### `depth_camera.xacro`
**Pfad:** `description/depth_camera.xacro`

**Was es ist:** Tiefenkamera-Definition für Gazebo Classic. Aktuell **auskommentiert**.

**Sensor:** 640×480 Tiefenbild, BGR, Clip 5 cm–8 m, Plugin `libgazebo_ros_camera.so`

**Verwendet von:** `robot.urdf.xacro` (auskommentiert – nicht aktiv)

---

### `face.xacro`
**Pfad:** `description/face.xacro`

**Was es ist:** Rein visueller Link. Simuliert ein „Gesicht" am vorderen Chassis-Ende.
Zwei Zylinder als „Augen" (schwarz) + großer Zylinder als „Mund" (rot).

**Verwendet von:** `robot.urdf.xacro` (immer eingebunden) — rein dekorativ.

---

### `nerf_launcher.xacro`
**Pfad:** `description/nerf_launcher.xacro`

**Was es ist:** Mount-Definition für den Nerf-Launcher. Bindet URDF aus `nerf_launch_system` ein
und verbindet dessen `bottom_plate`-Link mit dem Chassis.

**Montage:** `xyz="0.155 0 0.165"`, 90° gedreht um Z-Achse

**Verwendet von:** `robot.urdf.xacro` (immer eingebunden)
**Abhängigkeit:** Externes Paket `nerf_launch_system`

---

### `robot_core_bak.xml`
**Pfad:** `description/robot_core_bak.xml`

**Was es ist:** Backup/Archiv der ursprünglichen `robot_core`-Version (plain URDF, kein Xacro).
Wird **nicht** eingebunden. Gemäß Projekt-Konvention: bleibt bis zur expliziten Freigabe.

**Verwendet von:** Nirgends (archiviert)

---

## launch/ – Launch-Dateien

---

### `rsp.launch.py` *(Robot State Publisher)*
**Pfad:** `launch/rsp.launch.py`

**Was es ist:** Basislaunch-Datei. Verarbeitet `robot.urdf.xacro` mit `xacro` zur Laufzeit und
startet den `robot_state_publisher`.

**Gestarteter Node:** `robot_state_publisher` → publiziert `/robot_description` + TF-Baum

**Argumente:**

| Argument | Standard | Beschreibung |
|---|---|---|
| `use_sim_time` | `false` | Simulationszeit aktivieren |
| `use_ros2_control` | `true` | ros2_control-Block in URDF einbinden |
| `integrated_mode` | `false` | Nerf + Basis als ein System |
| `use_nerf_hardware` | `true` | Nerf-Hardware-Interface |
| `use_gazebo_classic` | `false` | Gazebo Classic statt Ignition |

**Verwendet von:** `launch_robot.launch.py`, `launch_sim.launch.py`, `gz_classic_launch_sim.launch.py`

---

### `launch_robot.launch.py` *(Echte Hardware – Basis)*
**Pfad:** `launch/launch_robot.launch.py`

**Was es ist:** Hauptlaunch für echten Roboter-Antrieb. Startet alle ros2_control-Komponenten
in **strikter Sequenz** (OnProcessExit-Chain) zur DDS-Überlastungsvermeidung.

**Start-Sequenz:**
```
[3s Delay] controller_manager
  └─(OnProcessStart)→ diff_drive_spawner
      └─(OnProcessExit)→ joint_broad_spawner
          └─(wenn use_nerf_hardware=true):
              trigger_controller → flywheel_controller
              → pusher_controller → arming_controller
              → nerf_control_node
```

**Gestartete Komponenten:**

| Komponente | Typ | Beschreibung |
|---|---|---|
| `rsp.launch.py` | Include | URDF + TF publizieren |
| `joystick.launch.py` | Include | Joystick-Eingabe |
| `twist_mux` | Node | Velocity-Multiplexer |
| `ros2_control_node` | Node | Controller Manager |
| `diff_cont` Spawner | Node | Differential-Drive-Controller |
| `joint_broad` Spawner | Node | Joint-State-Broadcaster |
| Nerf-Controller | Nodes (cond.) | trigger/flywheel/pusher/arming |
| `nerf_control_node` | Node (cond.) | High-Level Nerf-Steuerung |

**Argumente:** `use_nerf_hardware` (default: `false`), `auto_arm` (default: `false`)

**Verwendet von:** `launch_all_real.launch.py`

---

### `launch_all_real.launch.py` *(Echte Hardware – Vollständig)*
**Pfad:** `launch/launch_all_real.launch.py`

**Was es ist:** **Primärer Einstiegspunkt** für den echten Roboter. Kombiniert alle Subsysteme.

**Gestartete Komponenten:**

| Komponente | Bedingung | Beschreibung |
|---|---|---|
| `launch_robot.launch.py` | immer | Antrieb + Nerf |
| `rplidar.launch.py` | `launch_lidar=true` | RPLidar Scanner |
| `camera.launch.py` | `launch_camera=true` + `camera_type=v4l2` | v4l2-Kameratreiber |
| `real_camera.launch.py` | `launch_camera=true` + `camera_type=usb_cam` | usb_cam MJPEG |
| `face_tracker.launch.py` | `launch_face_tracker=true` | Gesichtserkennung (12s Delay) |

**Argumente:** `launch_lidar`, `launch_camera`, `camera_type` (v4l2/usb_cam),
`launch_face_tracker`, `target_person`, `allow_search`, `auto_arm`

**Typische Verwendung:**
```bash
ros2 launch gubot_one launch_all_real.launch.py
ros2 launch gubot_one launch_all_real.launch.py launch_camera:=true camera_type:=usb_cam launch_face_tracker:=true
```

---

### `launch_sim.launch.py` *(Ignition Gazebo Simulation)*
**Pfad:** `launch/launch_sim.launch.py`

**Was es ist:** Vollständige Simulation mit **Ignition Gazebo**. Startet Gazebo, spawnt den Roboter,
richtet den ROS↔Gazebo-Bridge ein und lädt alle Controller nach dem Spawn.

**Gestartete Komponenten:**

| Komponente | Beschreibung |
|---|---|
| `rsp.launch.py` | URDF + TF |
| `joystick.launch.py` | Joystick |
| `twist_mux` | Velocity-Multiplexer |
| `gz_sim.launch.py` | Ignition Gazebo starten |
| `ros_gz_sim create` | Roboter spawnen |
| `parameter_bridge` | ROS↔Ignition Topic-Bridge |
| `rviz2` | Visualisierung (`view_bot.rviz`) |
| Controller-Spawner | diff_cont, joint_broad, imu_broadcaster, Nerf-Controller |

**Bridge-Topics:** `/clock`, `/scan`, `/camera/image_raw`, `/camera/camera_info`, `/imu_sensor/imu_data`

**Umgebungsvariablen:** `MESA_GL_VERSION_OVERRIDE=4.5`, `GZ_TRANSPORT_RCVHWM=1000` (Software-Rendering)

**Argumente:** `world` (default: `obstacles.world`), `use_sim_time` (default: `true`)

---

### `gz_classic_launch_sim.launch.py` *(Gazebo Classic Simulation)*
**Pfad:** `launch/gz_classic_launch_sim.launch.py`

**Was es ist:** Wie `launch_sim.launch.py`, aber für **Gazebo Classic** (`gazebo_ros`).

**Unterschied zu `launch_sim.launch.py`:**

| Eigenschaft | Ignition | Gazebo Classic |
|---|---|---|
| Gazebo-Paket | `ros_gz_sim` | `gazebo_ros` |
| Spawn-Executable | `ros_gz_sim create` | `spawn_entity.py` |
| Bridge-Node | Ja (5 Topics) | Nein (integriert) |
| Standard-Welt | `obstacles.world` | `obstacles_classic.world` |

**Argumente:** `world` (default: `obstacles_classic.world`), `use_sim_time` (default: `true`)

---

### `joystick.launch.py`
**Pfad:** `launch/joystick.launch.py`

**Was es ist:** Startet die Joystick-Steuerung. `joy_node` kann optional lokal oder extern laufen.

**Nodes:**

| Node | Paket | Conditional | Beschreibung |
|---|---|---|---|
| `joy_node` | `joy` | `launch_joy_node=true` | Liest `/dev/input/js0` |
| `teleop_node` | `teleop_twist_joy` | immer | Joy → `/cmd_vel_joy` |
| `nerf_joy` | `gubot_one` | immer | Nerf-Steuerung via Controller |

**Topic-Flow:** `/dev/input/js0 → /joy → teleop_node → /cmd_vel_joy → twist_mux`

**Argumente:** `use_sim_time` (default: `false`), `launch_joy_node` (default: `true`)

**Konfiguration:** `config/joystick.yaml`

**Verwendet von:** `launch_robot.launch.py`, `launch_sim.launch.py`, `gz_classic_launch_sim.launch.py`

---

### `camera.launch.py` *(v4l2 Kameratreiber)*
**Pfad:** `launch/camera.launch.py`

**Was es ist:** Startet `v4l2_camera_node` für USB-Kamera. Optimiert für WLAN/Tailscale.

**Konfiguration:** `/dev/video0`, YUYV, 320×240, 10 FPS, Frame-ID: `camera_link_optical`

**Publizierte Topics:** `/camera/image_raw`, `/camera/camera_info`

**Verwendet von:** `launch_all_real.launch.py` (wenn `camera_type=v4l2`)

---

### `real_camera.launch.py` *(usb_cam Kameratreiber)*
**Pfad:** `launch/real_camera.launch.py`

**Was es ist:** Alternative Kamera mit `usb_cam` und MJPEG-Dekodierung.

**Konfiguration:** `/dev/video0`, `mjpeg2rgb`→`bgr8`, 320×240, 10 FPS

**Publizierte Topics:** `/camera/image_raw`, `/camera/camera_info`

**Kalibrierungsdatei:** `config/camera_info/real_cam.yaml`

**Verwendet von:** `launch_all_real.launch.py` (wenn `camera_type=usb_cam`)

---

### `rplidar.launch.py`
**Pfad:** `launch/rplidar.launch.py`

**Was es ist:** Startet den RPLidar-Treiber. Hardcodierter USB-Pfad für Raspberry Pi Hub-Port.

**Konfiguration:** Fester USB-by-path Port, `frame_id: laser_frame`, 360° Standard-Modus

**Publiziertes Topic:** `/scan`

**Verwendet von:** `launch_all_real.launch.py` (wenn `launch_lidar=true`)

---

### `navigation_launch.py` *(Nav2 Navigation Stack)*
**Pfad:** `launch/navigation_launch.py`

**Was es ist:** Vollständiger Nav2-Stack für autonome Navigation mit Lifecycle-Manager.

**Nodes:** `controller_server`, `planner_server`, `recoveries_server`,
`bt_navigator`, `waypoint_follower`, `lifecycle_manager_navigation`

**Argumente:** `use_sim_time`, `autostart` (default: `true`),
`params_file` (default: `config/nav2_params.yaml`), `default_bt_xml_filename`

---

### `localization_launch.py` *(AMCL Lokalisierung)*
**Pfad:** `launch/localization_launch.py`

**Was es ist:** Startet `map_server` und AMCL für Positionsschätzung in einer bekannten Karte.

**Nodes:** `map_server` (publiziert `/map`), `amcl` (Partikelfilter), `lifecycle_manager_localization`

**Argumente:** `map` (default: `maps/turtlebot3_world.yaml`), `use_sim_time`, `params_file`

---

### `online_async_launch.py` *(SLAM Toolbox)*
**Pfad:** `launch/online_async_launch.py`

**Was es ist:** Asynchrones Online-SLAM – erstellt gleichzeitig eine Karte und lokalisiert den Roboter.

**Node:** `slam_toolbox` (async_slam_toolbox_node)

**Konfiguration:** `config/mapper_params_online_async.yaml`

**Argumente:** `use_sim_time` (default: `true`), `params_file`

---

### `ball_tracker.launch.py`
**Pfad:** `launch/ball_tracker.launch.py`

**Was es ist:** Wrapper für externen `ball_tracker`. Wählt je nach `sim_mode` die passende Parameterdatei.

| sim_mode | Parameterdatei |
|---|---|
| `true` | `config/ball_tracker_params_sim.yaml` |
| `false` | `config/ball_tracker_params_robot.yaml` |

**Feste Argumente:** `image_topic=/camera/image_raw`, `cmd_vel_topic=/cmd_vel_tracker`, `enable_3d_tracker=true`

---

## Abhängigkeitsmatrix

### Welche Launch-Datei ruft wen auf?

```
launch_all_real.launch.py
  ├── launch_robot.launch.py
  │     ├── rsp.launch.py
  │     └── joystick.launch.py
  ├── rplidar.launch.py           (optional: launch_lidar=true)
  ├── camera.launch.py            (optional: camera_type=v4l2)
  ├── real_camera.launch.py       (optional: camera_type=usb_cam)
  └── ball_tracker/face_tracker   (optional: launch_face_tracker=true)

launch_sim.launch.py (Ignition)
  ├── rsp.launch.py
  └── joystick.launch.py

gz_classic_launch_sim.launch.py (Gazebo Classic)
  ├── rsp.launch.py
  └── joystick.launch.py
```

### Welche URDF-Dateien werden eingebunden?

```
robot.urdf.xacro  ← verarbeitet von: rsp.launch.py, launch_robot.launch.py
  ├── robot_core.xacro
  │     └── inertial_macros.xacro
  ├── ros2_control.xacro              (use_ros2_control=true, classic=false)
  ├── gz_classic_ros2_control.xacro   (use_ros2_control=true, classic=true)
  ├── gazebo_control.xacro            (use_ros2_control=false)
  ├── camera.xacro
  ├── face.xacro
  ├── nerf_launcher.xacro
  │     └── nerf_launch_system/.../launcher.urdf.xacro
  ├── [lidar.xacro]                   (auskommentiert)
  └── [depth_camera.xacro]            (auskommentiert)
```

### Externe Paket-Abhängigkeiten

| Paket | Verwendet in |
|---|---|
| `robot_state_publisher` | `rsp.launch.py` |
| `controller_manager` | `launch_robot.launch.py`, `launch_sim.launch.py` |
| `twist_mux` | `launch_robot.launch.py`, alle Sim-Launches |
| `joy` + `teleop_twist_joy` | `joystick.launch.py` |
| `ros_gz_sim` + `ros_gz_bridge` | `launch_sim.launch.py` |
| `gazebo_ros` | `gz_classic_launch_sim.launch.py` |
| `v4l2_camera` | `camera.launch.py` |
| `usb_cam` | `real_camera.launch.py` |
| `rplidar_ros` | `rplidar.launch.py` |
| `slam_toolbox` | `online_async_launch.py` |
| `nav2_*` | `navigation_launch.py`, `localization_launch.py` |
| `nerf_launch_system` | `nerf_launcher.xacro`, `launch_robot.launch.py` |
| `ball_tracker` | `ball_tracker.launch.py`, `launch_all_real.launch.py` |
| `diffdrive_arduino` | `ros2_control.xacro`, `gz_classic_ros2_control.xacro` |
| `ign_ros2_control` | `ros2_control.xacro` (Sim-Modus) |
| `gazebo_ros2_control` | `gz_classic_ros2_control.xacro` (Sim-Modus) |
