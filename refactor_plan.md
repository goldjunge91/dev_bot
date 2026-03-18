# gubot_one — Refactoring & Bereinigungsplan (v3)

> Dieses Dokument gilt als lebendiger Plan. Alle Änderungsschritte folgen den
> Regeln aus `copilot-instructions.md` (TDD, Kommentar-vor-Löschen, Linter-Checks).

---

## Konventionen (aus `copilot-instructions.md`)

Jeder Schritt in diesem Plan folgt diesen Regeln — keine Ausnahmen:

| Regel                     | Bedeutung                                                                                    |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| **TDD**                   | Erst fehlschlagenden Test schreiben, dann Änderung umsetzen                                  |
| **Test grün**             | Schritt gilt erst als erledigt, wenn alle Tests grün sind                                    |
| **Kommentar-vor-Löschen** | Alten Code auskommentieren, neuen direkt darunter — kein Hard-Delete ohne explizite Freigabe |
| **Linter**                | Nach jeder Phase `./test.sh` oder `ament_lint_common` lokal ausführen                        |
| **Naming**                | `snake_case` Dateien/Funktionen, `PascalCase` Klassen, `SCREAMING_SNAKE_CASE` Konstanten     |

> **Was "Kommentar-vor-Löschen" bei XACRO/Launch bedeutet:**
> Statt `rm` → zuerst Dateiinhalt leeren und einen Hinweiskommentar setzen,
> oder in den entsprechenden Include-Dateien den `<xacro:include>`-Aufruf
> auskommentieren. Erst nach expliziter Freigabe wirklich löschen.

---

## Zielarchitektur

Alle 4 Betriebsmodi laufen über **ros2_control** als einheitliche Schicht:

| Modus | Umgebung                         | ros2_control Plugin                          |
| ----- | -------------------------------- | -------------------------------------------- |
| **A** | Gazebo Harmonic / Ignition (Sim) | `gz_ros2_control/GazeboSimSystem`            |
| **B** | Gazebo Classic (Sim)             | `gazebo_ros2_control/GazeboSystem`           |
| **C** | Echte Hardware (Pico + Arduino)  | `diffdrive_arduino/DiffDriveArduinoHardware` |
| **D** | Fake Hardware (kein Gazebo)      | `mock_components/GenericSystem`              |

---

## Übersicht der Phasen

| Phase | Name                                   | Kern-Deliverable                           |
| ----- | -------------------------------------- | ------------------------------------------ |
| **1** | Duplikate aus `gubot_one` deaktivieren | `gubot_one` auf Metadaten reduziert        |
| **2** | Verwaiste Dateien deaktivieren         | Keine toten Dateien mehr aktiv eingebunden |
| **3** | Gazebo Classic reparieren              | Modus B startet sauber durch               |
| **4** | Sensoren vervollständigen              | IMU-Bridge, IMU-Filter, Lidar aktiv        |
| **5** | Nerf-Launcher reparieren               | Flywheel-Controller laden ohne Fehler      |
| **6** | Abschluss-Tests                        | Alle 4 Modi grün, Linter clean             |

---

## Phase 1 — Duplikate aus `gubot_one` deaktivieren

> **Ziel:** `gubot_one` enthält nach dieser Phase nur noch
> `package.xml`, `CMakeLists.txt`, `gubot_hardware.repos`, `gubot_simulation.repos`.

---

### Schritt 1.0 — Failing Test schreiben

**Datei (neu):** `src/gubot_one/test/test_package_structure.py`

```python
# test_package_structure.py
import os
import pytest

GUBOT_ONE_SRC = os.path.join(os.path.dirname(__file__), "..")

def test_no_description_folder_in_gubot_one():
    """gubot_one darf keinen description/-Ordner mit XACRO-Dateien enthalten."""
    desc_path = os.path.join(GUBOT_ONE_SRC, "description")
    xacro_files = []
    if os.path.isdir(desc_path):
        xacro_files = [f for f in os.listdir(desc_path) if f.endswith(".xacro")]
    assert xacro_files == [], \
        f"gubot_one/description/ enthält noch XACRO-Dateien: {xacro_files}"

def test_no_launch_files_in_gubot_one():
    """gubot_one darf keinen launch/-Ordner mit Launch-Dateien enthalten."""
    launch_path = os.path.join(GUBOT_ONE_SRC, "launch")
    launch_files = []
    if os.path.isdir(launch_path):
        launch_files = [f for f in os.listdir(launch_path) if f.endswith(".py")]
    assert launch_files == [], \
        f"gubot_one/launch/ enthält noch Launch-Dateien: {launch_files}"
```

Test ausführen → muss **rot** sein (Dateien existieren noch):
```bash
cd ~/projects/my_new_robot
python -m pytest src/gubot_one/test/test_package_structure.py -v
```

---

### Schritt 1.1 — XACRO-Duplikate auskommentieren / deaktivieren

**Dateien:**
```
src/gubot_one/description/robot_core.xacro
src/gubot_one/description/gz_classic_ros2_control.xacro
```

Da diese Dateien direkte XACRO-Dateien sind (kein Code), wird ihr gesamter Inhalt
durch einen Deaktivierungs-Header ersetzt:

```xml
<!--
  DEAKTIVIERT — siehe REFACTOR_PLAN.md Phase 1
  Kanonische Version: gubot_one_description/description/<dateiname>
  Freigabe zum Löschen: noch ausstehend
-->
```

Nach Freigabe:
```bash
rm src/gubot_one/description/robot_core.xacro
rm src/gubot_one/description/gz_classic_ros2_control.xacro
rmdir src/gubot_one/description/
```

---

### Schritt 1.2 — Launch-Duplikate auskommentieren

**Dateien:**
```
src/gubot_one/launch/launch_sim.launch.py
src/gubot_one/launch/gz_classic_launch_sim.launch.py
```

Dateiinhalt durch Platzhalter ersetzen:

```python
# DEAKTIVIERT — siehe REFACTOR_PLAN.md Phase 1
# Kanonische Version: gubot_one_bringup/launch/<dateiname>
# Freigabe zum Löschen: noch ausstehend
raise RuntimeError(
    "Diese Launch-Datei ist deaktiviert. "
    "Bitte gubot_one_bringup/launch/<dateiname> verwenden."
)
```

Nach Freigabe:
```bash
rm src/gubot_one/launch/launch_sim.launch.py
rm src/gubot_one/launch/gz_classic_launch_sim.launch.py
rmdir src/gubot_one/launch/
```

---

### Schritt 1.3 — Test ausführen → muss **grün** sein

```bash
python -m pytest src/gubot_one/test/test_package_structure.py -v
colcon test --packages-select gubot_one
```

Zielzustand `gubot_one`:
```
src/gubot_one/
├── package.xml
├── CMakeLists.txt
├── gubot_hardware.repos
├── gubot_simulation.repos
└── test/
    └── test_package_structure.py   ← NEU, grün
```

---

### Schritt 1.4 — Linter

```bash
cd ~/projects/my_new_robot && ./test.sh 2>&1 | grep -E "gubot_one|ERROR|FAIL"
```

---

## Phase 2 — Verwaiste Dateien deaktivieren

---

### Schritt 2.0 — Failing Tests schreiben

**Datei (neu):** `src/gubot_one_description/test/test_no_orphan_files.py`

```python
# test_no_orphan_files.py
import os
import pytest

DESC = os.path.join(os.path.dirname(__file__), "..", "description")

def test_no_backup_xml():
    """Keine manuellen Backup-Dateien im description/-Ordner."""
    bak_files = [f for f in os.listdir(DESC) if "_bak" in f or f.endswith(".bak")]
    assert bak_files == [], f"Backup-Dateien gefunden: {bak_files}"

def test_no_gazebo_control_xacro():
    """gazebo_control.xacro (libgazebo_ros_diff_drive, veraltet) darf nicht aktiv sein."""
    path = os.path.join(DESC, "gazebo_control.xacro")
    if os.path.exists(path):
        content = open(path).read().strip()
        assert content.startswith("<!--") and "DEAKTIVIERT" in content, \
            "gazebo_control.xacro ist noch aktiv (kein DEAKTIVIERT-Header)"
```

Test ausführen → muss **rot** sein.

---

### Schritt 2.1 — `gazebo_control.xacro` deaktivieren

Inhalt ersetzen durch:

```xml
<!--
  DEAKTIVIERT — siehe REFACTOR_PLAN.md Phase 2
  Grund: libgazebo_ros_diff_drive.so umgeht ros2_control komplett.
  Alle 4 Betriebsmodi nutzen ros2_control — dieses Plugin wird nie gebraucht.
  Freigabe zum Löschen: noch ausstehend
-->

<!--  ORIGINAL-INHALT (auskommentiert):
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
    <gazebo>
        <plugin name="diff_drive" filename="libgazebo_ros_diff_drive.so">
            ...
        </plugin>
    </gazebo>
</robot>
-->
```

---

### Schritt 2.2 — `robot_core_bak.xml` deaktivieren

```xml
<!--
  DEAKTIVIERT — manuelles Backup, gehört nicht ins Repository.
  Versionierung erfolgt über Git.
  Freigabe zum Löschen: noch ausstehend
-->
```

---

### Schritt 2.3 — Doppelte World-Dateien in `nerf_launch_system` deaktivieren

**Failing Test (neu):** `src/nerf_launch_system/test/test_no_sim_worlds.py`

```python
# test_no_sim_worlds.py
import os
import pytest

NLS_ROOT = os.path.join(os.path.dirname(__file__), "..")

def test_no_worlds_folder():
    """nerf_launch_system ist ein HW-Interface-Paket, kein Sim-Paket.
    Worlds gehören zentral nach gubot_gazebo/worlds/."""
    worlds_path = os.path.join(NLS_ROOT, "worlds")
    world_files = []
    if os.path.isdir(worlds_path):
        world_files = [f for f in os.listdir(worlds_path) if f.endswith(".world")]
    assert world_files == [], \
        f"nerf_launch_system/worlds/ enthält noch World-Dateien: {world_files}"
```

Vor dem Löschen — Inhalt vergleichen:
```bash
diff src/nerf_launch_system/worlds/obstacles.world src/gubot_gazebo/worlds/obstacles.world
diff src/nerf_launch_system/worlds/empty.world     src/gubot_gazebo/worlds/empty.world
```

Wenn identisch — Dateien durch Hinweis-Textdatei ersetzen:
```
# DEAKTIVIERT
# Kanonische Version: gubot_gazebo/worlds/<dateiname>
# Freigabe zum Löschen: noch ausstehend
```

`src/nerf_launch_system/launch/simulate.launch.py` — World-Pfad anpassen:
```python
# VORHER (auskommentiert):
# get_package_share_directory("nerf_launch_system"), "worlds", "obstacles.world"

# NACHHER:
get_package_share_directory("gubot_gazebo"), "worlds", "obstacles.world"
```

---

### Schritt 2.4 — Doppelte `gazebo_params.yaml` deaktivieren

```bash
diff src/nerf_launch_system/config/gazebo_params.yaml \
     src/gubot_one_bringup/config/gazebo_params.yaml
```

Wenn identisch — Datei durch Hinweis ersetzen:
```yaml
# DEAKTIVIERT — Duplikat von gubot_one_bringup/config/gazebo_params.yaml
# Freigabe zum Löschen: noch ausstehend
```

---

### Schritt 2.5 — Tests grün + Linter

```bash
python -m pytest src/gubot_one_description/test/test_no_orphan_files.py -v
python -m pytest src/nerf_launch_system/test/test_no_sim_worlds.py -v
./test.sh 2>&1 | grep -E "ERROR|FAIL|WARN"
```

---

## Phase 3 — Gazebo Classic reparieren

---

### Schritt 3.0 — Failing Tests schreiben

**Datei (neu):** `src/gubot_one_bringup/test/test_classic_launch_args.py`

```python
# test_classic_launch_args.py
import subprocess
import pytest

def test_robot_classic_urdf_xacro_valid():
    """robot_classic.urdf.xacro muss zu gültigem URDF prozessiert werden können."""
    result = subprocess.run(
        ["ros2", "run", "xacro", "xacro",
         "src/gubot_one_description/description/robot_classic.urdf.xacro",
         "integrated_mode:=true"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"xacro fehlgeschlagen:\n{result.stderr}"
    assert "<robot" in result.stdout, "URDF enthält kein <robot>-Element"
    assert "gazebo_ros2_control/GazeboSystem" in result.stdout, \
        "Classic-URDF lädt nicht das richtige ros2_control-Plugin"
    assert "gz_ros2_control/GazeboSimSystem" not in result.stdout, \
        "Classic-URDF lädt fälschlicherweise das Ignition-Plugin"

def test_classic_camera_plugin_present():
    """robot_classic.urdf.xacro muss libgazebo_ros_camera.so einbinden."""
    result = subprocess.run(
        ["ros2", "run", "xacro", "xacro",
         "src/gubot_one_description/description/robot_classic.urdf.xacro",
         "integrated_mode:=true"],
        capture_output=True, text=True
    )
    assert "libgazebo_ros_camera.so" in result.stdout, \
        "Kein libgazebo_ros_camera.so in Classic-URDF gefunden"

def test_classic_config_path_correct():
    """gz_classic_ros2_control.xacro darf nicht auf gubot_one/config zeigen."""
    with open("src/gubot_one_description/description/gz_classic_ros2_control.xacro") as f:
        content = f.read()
    assert "$(find gubot_one)/config" not in content, \
        "Falscher Config-Pfad: $(find gubot_one)/config gefunden"
    assert "$(find gubot_one_bringup)/config" in content, \
        "Korrekter Config-Pfad $(find gubot_one_bringup)/config fehlt"
```

Test ausführen → muss **rot** sein.

---

### Schritt 3.1 — `rsp_classic.launch.py` erstellen (neue Datei)

**Datei (neu):** `src/gubot_one_bringup/launch/rsp_classic.launch.py`

Lädt `robot_classic.urdf.xacro` statt `robot.urdf.xacro`:

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    use_sim_time      = LaunchConfiguration("use_sim_time")
    integrated_mode   = LaunchConfiguration("integrated_mode")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")

    pkg_path   = get_package_share_directory("gubot_one_description")
    xacro_file = os.path.join(pkg_path, "description", "robot_classic.urdf.xacro")

    robot_description_config = Command([
        "xacro ", xacro_file,
        " integrated_mode:=", integrated_mode,
        " use_nerf_hardware:=", use_nerf_hardware,
    ])

    params = {
        "robot_description": ParameterValue(robot_description_config, value_type=str),
        "use_sim_time": use_sim_time,
    }

    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time",      default_value="false"),
        DeclareLaunchArgument("integrated_mode",   default_value="false"),
        DeclareLaunchArgument("use_nerf_hardware", default_value="true"),
        node_robot_state_publisher,
    ])
```

---

### Schritt 3.2 — `gz_classic_launch_sim.launch.py` auf `rsp_classic` umstellen

```python
# gz_classic_launch_sim.launch.py — RSP-Include

# VORHER (auskommentiert):
# os.path.join(get_package_share_directory(package_name), "launch", "rsp.launch.py")

# NACHHER:
os.path.join(get_package_share_directory(package_name), "launch", "rsp_classic.launch.py")
```

---

### Schritt 3.3 — Kamera in `camera.xacro` für Classic erweitern

**Datei:** `src/gubot_one_description/description/camera.xacro`

```xml
<!-- camera.xacro — bestehenden <gazebo reference="camera_link">-Block ersetzen -->

<!-- VORHER (auskommentiert): -->
<!--
<gazebo reference="camera_link">
    <material>Gazebo/Black</material>
    <sensor name="camera" type="camera">
        ...
        <topic>camera/image_raw</topic>
    </sensor>
</gazebo>
-->

<!-- NACHHER: -->
<xacro:arg name="use_gazebo_classic" default="false"/>

<gazebo reference="camera_link">
    <material>Gazebo/Black</material>

    <!-- Ignition / Harmonic -->
    <xacro:unless value="$(arg use_gazebo_classic)">
        <sensor name="camera" type="camera">
            <pose>0 0 0 0 0 0</pose>
            <visualize>false</visualize>
            <update_rate>10</update_rate>
            <camera>
                <horizontal_fov>1.089</horizontal_fov>
                <image>
                    <format>R8G8B8</format>
                    <width>640</width>
                    <height>480</height>
                </image>
                <clip><near>0.05</near><far>8.0</far></clip>
            </camera>
            <topic>camera/image_raw</topic>
        </sensor>
    </xacro:unless>

    <!-- Gazebo Classic -->
    <xacro:if value="$(arg use_gazebo_classic)">
        <sensor type="camera" name="camera">
            <update_rate>10</update_rate>
            <camera>
                <horizontal_fov>1.089</horizontal_fov>
                <image>
                    <format>R8G8B8</format>
                    <width>640</width>
                    <height>480</height>
                </image>
                <clip><near>0.05</near><far>8.0</far></clip>
            </camera>
            <plugin name="camera_controller" filename="libgazebo_ros_camera.so">
                <ros>
                    <remapping>image_raw:=camera/image_raw</remapping>
                    <remapping>camera_info:=camera/camera_info</remapping>
                </ros>
                <frame_name>camera_link_optical</frame_name>
            </plugin>
        </sensor>
    </xacro:if>
</gazebo>
```

---

### Schritt 3.4 — Config-Pfad-Bug fixen

**Datei:** `src/gubot_one_description/description/gz_classic_ros2_control.xacro`

```xml
<!-- VORHER (auskommentiert): -->
<!-- <parameters>$(find gubot_one)/config/my_controllers.yaml</parameters> -->
<!-- <parameters>$(find gubot_one)/config/gaz_ros2_ctl_use_sim.yaml</parameters> -->

<!-- NACHHER: -->
<parameters>$(find gubot_one_bringup)/config/my_controllers.yaml</parameters>
<parameters>$(find gubot_one_bringup)/config/gaz_ros2_ctl_use_sim.yaml</parameters>
```

---

### Schritt 3.5 — Tests grün + Linter

```bash
cd ~/projects/my_new_robot
source install/setup.bash
python -m pytest src/gubot_one_bringup/test/test_classic_launch_args.py -v
colcon test --packages-select gubot_one_bringup gubot_one_description
./test.sh 2>&1 | grep -E "ERROR|FAIL"
```

---

## Phase 4 — Sensoren vervollständigen

---

### Schritt 4.0 — Failing Tests schreiben

**Datei (neu):** `src/gubot_one_bringup/test/test_sensor_config.py`

```python
# test_sensor_config.py
import ast
import os
import pytest


def _read_launch(filename):
    path = os.path.join(
        os.path.dirname(__file__), "..", "launch", filename
    )
    return open(path).read()


def test_imu_bridge_active_in_ignition_launch():
    """IMU-Bridge darf in launch_sim.launch.py nicht auskommentiert sein."""
    content = _read_launch("launch_sim.launch.py")
    assert '"/imu_sensor/imu_data@sensor_msgs/msg/Imu[gz.msgs.IMU"' in content, \
        "IMU-Bridge-Eintrag fehlt oder ist auskommentiert in launch_sim.launch.py"


def test_imu_filter_present_in_classic_launch():
    """imu_filter_madgwick_node muss in gz_classic_launch_sim.launch.py vorhanden sein."""
    content = _read_launch("gz_classic_launch_sim.launch.py")
    assert "imu_filter_madgwick" in content, \
        "imu_filter_madgwick fehlt in gz_classic_launch_sim.launch.py"


def test_imu_z_position_canonical():
    """IMU-Z-Position muss in robot_core.xacro 0.148 sein."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "gubot_one_description",
        "description", "robot_core.xacro"
    )
    content = open(path).read()
    # Suche nach imu_joint origin — muss 0.148 enthalten, nicht 0.05
    assert 'xyz="0 0 0.148"' in content, \
        "IMU Z-Position in robot_core.xacro ist nicht 0.148"
```

Test ausführen → muss **rot** sein.

---

### Schritt 4.1 — IMU-Bridge aktivieren

**Datei:** `src/gubot_one_bringup/launch/launch_sim.launch.py`

```python
# VORHER (auskommentiert):
# "/imu_sensor/imu_data@sensor_msgs/msg/Imu[gz.msgs.IMU",

# NACHHER:
"/imu_sensor/imu_data@sensor_msgs/msg/Imu[gz.msgs.IMU",
```

---

### Schritt 4.2 — IMU-Filter in Classic-Launch ergänzen

**Datei:** `src/gubot_one_bringup/launch/gz_classic_launch_sim.launch.py`

```python
# NEU — direkt nach dem spawn_entity-Block einfügen:
imu_filter_node = Node(
    package="imu_filter_madgwick",
    executable="imu_filter_madgwick_node",
    name="imu_filter",
    output="screen",
    parameters=[{
        "use_sim_time": True,
        "use_mag": False,
        "publish_tf": False,
        "world_frame": "enu",
        "fixed_frame": "odom",
        "gain": 0.01,
        "zeta": 0.0,
    }],
    remappings=[
        ("/imu/data_raw", "/imu_broadcaster/imu"),
        ("/imu/data", "/imu/data"),
    ],
)
# + imu_filter_node zur LaunchDescription-Liste hinzufügen
```

---

### Schritt 4.3 — IMU-Z-Position vereinheitlichen

**Datei:** `src/gubot_one_description/description/robot_core.xacro`

```xml
<!-- VORHER (auskommentiert): -->
<!-- <origin xyz="0 0 0.05" rpy="0 0 0"/> -->

<!-- NACHHER: -->
<origin xyz="0 0 0.148" rpy="0 0 0"/>
```

---

### Schritt 4.4 — Lidar aktivieren

**Datei:** `src/gubot_one_description/description/robot.urdf.xacro`

```xml
<!-- VORHER (auskommentiert): -->
<!-- <xacro:include filename="lidar.xacro" /> -->

<!-- NACHHER: -->
<xacro:include filename="lidar.xacro" />
```

Gleiches in `robot_classic.urdf.xacro`.

---

### Schritt 4.5 — Tests grün + Linter

```bash
python -m pytest src/gubot_one_bringup/test/test_sensor_config.py -v
colcon test --packages-select gubot_one_bringup gubot_one_description
./test.sh 2>&1 | grep -E "ERROR|FAIL"
```

---

## Phase 5 — Nerf-Launcher reparieren

---

### Schritt 5.0 — Failing Tests schreiben

**Datei (neu):** `src/nerf_launch_system/test/test_launcher_urdf.py`

```python
# test_launcher_urdf.py
import subprocess
import pytest


def test_flywheel_joints_are_continuous():
    """flywheel_left_joint und flywheel_right_joint müssen 'continuous' sein."""
    result = subprocess.run(
        ["ros2", "run", "xacro", "xacro",
         "src/nerf_launch_system/description/urdf/launcher.urdf.xacro",
         "integrated_mode:=true"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"xacro fehlgeschlagen:\n{result.stderr}"
    # Zähle wie oft type="fixed" nach flywheel vorkommt
    import re
    fixed_flywheel = re.findall(
        r'name="flywheel_(left|right)_joint"[^>]*type="fixed"', result.stdout
    )
    assert fixed_flywheel == [], \
        f"Flywheel-Joints sind noch 'fixed': {fixed_flywheel}"


def test_no_trigger_joint_in_classic_hw_xacro():
    """trigger_joint existiert nicht im URDF — darf nicht in HW-ros2_control stehen."""
    with open(
        "src/gubot_one_description/description/gz_classic_ros2_control.xacro"
    ) as f:
        content = f.read()
    # trigger_joint darf nur in einem Kommentar vorkommen
    import re
    active_trigger = re.findall(r'(?<!--.*)<joint name="trigger_joint"', content)
    assert active_trigger == [], \
        "trigger_joint ist noch aktiv in gz_classic_ros2_control.xacro"
```

Test ausführen → muss **rot** sein.

---

### Schritt 5.1 — Flywheel-Joints auf `continuous` umstellen

**Datei:** `src/nerf_launch_system/description/urdf/launcher.urdf.xacro`

```xml
<!-- VORHER (auskommentiert): -->
<!--
<joint name="flywheel_right_joint" type="fixed">
    <origin xyz="0.0 -7.800000000000029e-06 -0.0175"
            rpy="1.5707963267948966 -7.224685652388453e-18 -2.3543024464062444e-21" />
    <parent link="motor_right" />
    <child link="flywheel_right" />
</joint>
<joint name="flywheel_left_joint" type="fixed">
    <origin xyz="0.0 -7.810000000000317e-06 -0.0175"
            rpy="1.5707963267948966 -1.0870161501361781e-16 -2.35430244640625e-21" />
    <parent link="motor_left" />
    <child link="flywheel_left" />
</joint>
-->

<!-- NACHHER: -->
<joint name="flywheel_right_joint" type="continuous">
    <origin xyz="0.0 -7.800000000000029e-06 -0.0175"
            rpy="1.5707963267948966 0 0" />
    <parent link="motor_right" />
    <child link="flywheel_right" />
    <axis xyz="0 0 1"/>
    <limit effort="1.0" velocity="500.0"/>
    <dynamics damping="0.01" friction="0.0"/>
</joint>

<joint name="flywheel_left_joint" type="continuous">
    <origin xyz="0.0 -7.810000000000317e-06 -0.0175"
            rpy="1.5707963267948966 0 0" />
    <parent link="motor_left" />
    <child link="flywheel_left" />
    <axis xyz="0 0 1"/>
    <limit effort="1.0" velocity="500.0"/>
    <dynamics damping="0.01" friction="0.0"/>
</joint>
```

---

### Schritt 5.2 — Joint-Namen in Classic-HW-Branch bereinigen

**Datei:** `src/gubot_one_description/description/gz_classic_ros2_control.xacro`
(Hardware-Branch `<xacro:unless value="$(arg sim_mode)">`)

```xml
<!-- VORHER (auskommentiert): -->
<!--
<joint name="trigger_joint">
    <command_interface name="position"/>
    <state_interface name="position"/>
</joint>
<joint name="dart_pusher_joint">
    <command_interface name="velocity"/>
    <state_interface name="velocity"/>
</joint>
-->

<!-- NACHHER — korrekte Joint-Namen laut launcher.urdf.xacro: -->
<joint name="tilt_joint">
    <command_interface name="position"/>
    <state_interface name="position"/>
</joint>
<joint name="shooter_joint">
    <command_interface name="position"/>
    <state_interface name="position"/>
</joint>
<joint name="flywheel_left_joint">
    <command_interface name="velocity"/>
    <state_interface name="velocity"/>
</joint>
<joint name="flywheel_right_joint">
    <command_interface name="velocity"/>
    <state_interface name="velocity"/>
</joint>
<joint name="system_arming_joint">
    <command_interface name="position"/>
    <state_interface name="position"/>
</joint>
```

---

### Schritt 5.3 — Tests grün + Linter

```bash
python -m pytest src/nerf_launch_system/test/test_launcher_urdf.py -v
colcon test --packages-select nerf_launch_system gubot_one_description
./test.sh 2>&1 | grep -E "ERROR|FAIL"
```

---

## Phase 6 — Abschluss-Tests (alle 4 Modi)

### Schritt 6.1 — Vollständiger Build

```bash
cd ~/projects/my_new_robot
colcon build --symlink-install
source install/setup.bash
```

---

### Schritt 6.2 — URDF-Validierung (alle Modi)

```bash
# Modus A
ros2 run xacro xacro src/gubot_one_description/description/robot.urdf.xacro \
  sim_mode:=true use_ros2_control:=true integrated_mode:=true \
  > /tmp/robot_a.urdf && check_urdf /tmp/robot_a.urdf

# Modus B
ros2 run xacro xacro src/gubot_one_description/description/robot_classic.urdf.xacro \
  integrated_mode:=true > /tmp/robot_b.urdf && check_urdf /tmp/robot_b.urdf

# Modus C (echte Hardware — nur URDF prüfen, kein Start)
ros2 run xacro xacro src/gubot_one_description/description/robot.urdf.xacro \
  sim_mode:=false use_ros2_control:=true use_fake_hardware:=false \
  > /tmp/robot_c.urdf && check_urdf /tmp/robot_c.urdf

# Modus D
ros2 run xacro xacro src/gubot_one_description/description/robot.urdf.xacro \
  sim_mode:=false use_ros2_control:=true use_fake_hardware:=true \
  > /tmp/robot_d.urdf && check_urdf /tmp/robot_d.urdf
```

---

### Schritt 6.3 — Modus A: Gazebo Harmonic

```bash
ros2 launch gubot_one_bringup launch_sim.launch.py
```

- [ ] Robot erscheint in Gazebo
- [ ] `/camera/image_raw` publiziert
- [ ] `/imu_broadcaster/imu` publiziert
- [ ] `/imu/data` (Madgwick) publiziert
- [ ] `/scan` publiziert
- [ ] `diff_cont`, `joint_broad`, `imu_broadcaster` aktiv
- [ ] `tilt_controller`, `shooter_controller`, `arming_controller` aktiv

---

### Schritt 6.4 — Modus B: Gazebo Classic

```bash
ros2 launch gubot_one_bringup gz_classic_launch_sim.launch.py
```

- [ ] Robot erscheint in Gazebo Classic
- [ ] `gazebo_ros2_control/GazeboSystem` (nicht `gz_ros2_control`) geladen
- [ ] `/camera/image_raw` publiziert
- [ ] `/imu/data` publiziert
- [ ] Controller aktiv

---

### Schritt 6.5 — Modus D: Fake Hardware

```bash
ros2 launch gubot_one_bringup launch_robot.launch.py use_fake_hardware:=true
```

- [ ] `mock_components/GenericSystem` geladen
- [ ] Controller aktiv
- [ ] Teleop-Befehle verarbeitet

---

### Schritt 6.6 — Face Tracker

```bash
ros2 launch face_tracker face_tracker_sim.launch.py
```

- [ ] `detect_face` empfängt `/camera/image_raw`
- [ ] `follow_face` sendet tilt-Kommandos
- [ ] `fire_at_face` sendet Schuss-Kommandos

---

### Schritt 6.7 — Alle Tests + Linter final

```bash
colcon test
./test.sh
colcon test-result --all | grep -E "FAIL|ERROR"
```

Alle Tests **grün**, Linter **clean** → Refactoring abgeschlossen.

---

## Freigaben zum endgültigen Löschen

Folgende Dateien wurden auskommentiert/deaktiviert und warten auf explizite Freigabe:

| Datei                                                    | Deaktiviert in Phase | Freigabe     |
| -------------------------------------------------------- | -------------------- | ------------ |
| `gubot_one/description/robot_core.xacro`                 | 1                    | ⬜ ausstehend |
| `gubot_one/description/gz_classic_ros2_control.xacro`    | 1                    | ⬜ ausstehend |
| `gubot_one/launch/launch_sim.launch.py`                  | 1                    | ⬜ ausstehend |
| `gubot_one/launch/gz_classic_launch_sim.launch.py`       | 1                    | ⬜ ausstehend |
| `gubot_one_description/description/gazebo_control.xacro` | 2                    | ⬜ ausstehend |
| `gubot_one_description/description/robot_core_bak.xml`   | 2                    | ⬜ ausstehend |
| `nerf_launch_system/worlds/obstacles.world`              | 2                    | ⬜ ausstehend |
| `nerf_launch_system/worlds/empty.world`                  | 2                    | ⬜ ausstehend |
| `nerf_launch_system/config/gazebo_params.yaml`           | 2                    | ⬜ ausstehend |

---

## Zielzustand — Paketverantwortlichkeit

```
src/
├── gubot_one/                ← package.xml, CMakeLists.txt, *.repos
│
├── gubot_one_description/    ← EINZIGE Quelle für URDF/XACRO
│   └── description/
│       ├── robot.urdf.xacro              (Modi A, C, D)
│       ├── robot_classic.urdf.xacro      (Modus B)
│       ├── robot_core.xacro              (Basis, IMU bei Z=0.148)
│       ├── ros2_control.xacro            (Harmonic + HW + Fake)
│       ├── gz_classic_ros2_control.xacro (Classic Sim + HW, korr. Pfade)
│       ├── camera.xacro                  (Harmonic + Classic Branch)
│       ├── lidar.xacro                   (aktiv)
│       ├── depth_camera.xacro            (optional, Phase 7+)
│       ├── face.xacro
│       └── nerf_launcher.xacro
│
├── gubot_one_bringup/        ← EINZIGE Quelle für Launches & Config
│   ├── launch/
│   │   ├── launch_sim.launch.py             (Modus A)
│   │   ├── gz_classic_launch_sim.launch.py  (Modus B)
│   │   ├── launch_robot.launch.py           (Modus C + D)
│   │   ├── rsp.launch.py                    (Harmonic/HW)
│   │   └── rsp_classic.launch.py            (Classic) ← NEU
│   └── config/
│
├── gubot_gazebo/             ← Gazebo-Welten & Sim-Env-Config (zentral)
├── nerf_launch_system/       ← HW-Interface C++, Firmware, Launcher-URDF
└── face_tracker/             ← Erkennung, Verfolgung, Schussauslösung
```