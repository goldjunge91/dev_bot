# Fix: Gazebo Classic – Mesh-Pfade & Rotierende Räder

## Ansatz: Separate Dateien per Simulator

Statt kombinierter Dateien mit `use_gazebo_classic`-Guards bekommt jede Simulationsumgebung ihre **eigenen, unabhängigen Dateien**.

| Umgebung | URDF-Einstieg | ros2_control | Status |
|---|---|---|---|
| **Gazebo Classic** | `robot_classic.urdf.xacro` **(NEU)** | [gz_classic_ros2_control.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one/description/gz_classic_ros2_control.xacro) (aufgeteilt) | Wird gefixt |
| **Gazebo Harmonic** | [robot.urdf.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one_description/description/robot.urdf.xacro) (unverändert) | [ros2_control.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one/description/gz_classic_ros2_control.xacro) (unverändert) | Bleibt wie es ist |
| **Real Hardware** | [robot.urdf.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one_description/description/robot.urdf.xacro) (unverändert) | [ros2_control.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one/description/gz_classic_ros2_control.xacro) (unverändert) | Bleibt wie es ist |

> [!IMPORTANT]
> Das Harmonic-Setup ([simulation.launch.py](file:///home/ros/projects/my_new_robot/src/gubot_gazebo/launch/simulation.launch.py), [robot.urdf.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one_description/description/robot.urdf.xacro), [ros2_control.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one/description/gz_classic_ros2_control.xacro)) wird **nicht angefasst**.

## Problembeschreibung

### 1. Mesh-Pfade nicht gefunden
`GAZEBO_MODEL_PATH` in `gubot_gazebo/gz_classic_launch_sim.launch.py` fehlt der Eintrag für `install/nerf_launch_system/share`. Vorhanden: `GAZEBO_RESOURCE_PATH` (Zeile 342), aber Gazebo Classic löst `model://nerf_launch_system/...` nur via `GAZEBO_MODEL_PATH` auf.

### 2. Räder drehen sich unkontrolliert
Roboter spawnt mit `-z 0.1`, fällt auf den Boden → Aufprall gibt ~6.6 rad/s Impuls auf Räder. Gelenk-Dämpfung (`damping=0.3`) ist zu niedrig um das abzufangen.

## Proposed Changes

---

### Classic-spezifische XACRO-Dateien

#### [NEW] `robot_classic.urdf.xacro` in `gubot_one_description/description/`

Eigenständiger Einstiegspunkt für Gazebo Classic. Inkludiert direkt `robot_core_classic.xacro` (kein Flag-Parameter), `gz_classic_ros2_control_sim.xacro` und `nerf_launcher.xacro`.

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="robot">
    <xacro:include filename="robot_core_classic.xacro" />
    <xacro:include filename="gz_classic_ros2_control_sim.xacro" />
    <xacro:include filename="nerf_launcher.xacro" />
</robot>
```

#### [NEW] `robot_core_classic.xacro` in `gubot_one_description/description/`

Kopie von `robot_core.xacro` mit:
- **Damping erhöht**: `damping="5.0" friction="1.5"` (statt `0.3`/`0.2`) für beide Räder
- **IMU-Plugin direkt** ohne `use_gazebo_classic`-Guard (Classic-Plugin ist dauerhaft aktiv)
- **Keine `xacro:if/unless`** – alles direkt für Classic dediziert

#### [NEW] `gz_classic_ros2_control_sim.xacro` in `gubot_one_description/description/`

Extrahiert aus `gz_classic_ros2_control.xacro`: **nur** der `sim_mode=true` Block (GazeboSystem) ohne den Real-Hardware-Block. Kein `xacro:if`/`xacro:unless` mehr nötig.

---

### Launch-Dateien

#### [MODIFY] [gz_classic_launch_sim.launch.py](file:///home/ros/projects/my_new_robot/src/gubot_gazebo/launch/gz_classic_launch_sim.launch.py)

**Fix 1 – GAZEBO_MODEL_PATH** (Zeile 334, nach `~/.gazebo/models`):
```python
AppendEnvironmentVariable(
    "GAZEBO_MODEL_PATH",
    os.path.join(os.getcwd(), "install", "nerf_launch_system", "share"),
),
AppendEnvironmentVariable(
    "GAZEBO_MODEL_PATH",
    os.path.join(os.getcwd(), "src"),
),
```

**Fix 2 – RSP nutzt neuen Classic-Einstieg**: RSP-Include erhält `xacro_file` auf `robot_classic.urdf.xacro` via neues `rsp_classic.launch.py` (kein `use_gazebo_classic` Flag mehr nötig).

#### [NEW] `rsp_classic.launch.py` in `gubot_one_bringup/launch/`

Vereinfachte Version von `rsp.launch.py`: Lädt direkt `robot_classic.urdf.xacro`, ohne `use_gazebo_classic`/`use_nerf_hardware` Parameter.

---

## Verification Plan

### Build
```bash
colcon build --packages-select gubot_one_description gubot_one_bringup gubot_gazebo
source install/setup.bash
```

### Mesh-Test
```bash
ros2 launch gubot_gazebo gz_classic_launch_sim.launch.py
# Erwartung: KEINE "URI not supported by Fuel" Warnungen für nerf_launch_system meshes
```

### Rad-Stillstand-Test
Nach dem Spawn ~5s warten ohne Fahrbefehl:
```bash
ros2 topic echo /joint_states --once | grep -A3 "left_wheel\|right_wheel"
# Erwartung: velocity nahe 0.0
```
