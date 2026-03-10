# Phase 2: Der Startpunkt (Launch-Dateien) im Detail

Die Launch-Dateien sind der Startknopf für deinen Roboter. Anstatt 10 verschiedene Terminals zu öffnen und Nodes manuell zu starten, bündelt eine Launch-Datei (in Python geschrieben) alles.

Wir schauen uns deine Dateien `launch_sim.launch.py`, `rsp.launch.py` und `joystick.launch.py` aus dem Paket `gubot_one` genauer an.

## 1. Das Grundgerüst jeder Launch-Datei
Jede ROS 2 Python Launch-Datei muss eine Funktion namens `generate_launch_description()` haben. Am Ende dieser Funktion wird eine große Liste (`LaunchDescription([...])`) zurückgegeben, die alle Befehle enthält, die ROS 2 abarbeiten soll.

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # ... hier passiert die Magie ...
    
    return LaunchDescription([
        # Eine Liste aller Dinge, die gestartet werden sollen
    ])
```

## 2. Argumente und Variablen
Oft willst du beim Start Parameter übergeben, z.B. `ros2 launch gubot_one rsp.launch.py use_sim_time:=true`.
Dafür gibt es zwei Bausteine in ROS 2:
1. **`LaunchConfiguration("Name")`**: Liest den Wert aus, während die Launch-Datei läuft (Das ist wie eine Variable).
2. **`DeclareLaunchArgument(...)`**: Definiert, dass dieses Argument überhaupt existiert und was der Standardwert ist.

*Beispiel:*
```python
use_sim_time = LaunchConfiguration("use_sim_time")

declare_use_sim_time_cmd = DeclareLaunchArgument(
    "use_sim_time",
    default_value="true",
    description="Use sim time if true",
)
```

## 3. Nodes starten (Das Arbeiter-Programm)
Ein **Node** ist ein eigenständiges Programm. Um es zu starten, sagst du ROS 2 genau, wo das Programm liegt.
In deiner `joystick.launch.py` siehst du zum Beispiel das hier:

```python
    joy_node = Node(
        package="joy",
        executable="joy_node",
        parameters=[joy_params, {"use_sim_time": use_sim_time}],
        condition=if_condition.IfCondition(launch_joy_node),
    )
```
- `package="joy"`: Suche im Paket "joy".
- `executable="joy_node"`: Führe die Datei "joy_node" aus.
- `parameters=[...]`: Übergib eine Datei (`joy_params`) und Variablen (`use_sim_time`).
- `condition=...`: (Optional) Starte diesen Node nur, wenn eine bestimmte Bedingung (`launch_joy_node` = true) erfüllt ist.

## 4. Andere Launch-Dateien einbinden (Include)
Roboter sind komplex. Es ist schlechter Stil, alles in eine riesige Launch-Datei zu schreiben. Stattdessen ruft eine Hautpdatei (wie `launch_sim.launch.py`) andere Unter-Dateien (wie `rsp.launch.py`) auf. 

Das nennt sich **`IncludeLaunchDescription`**:

```python
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(get_package_share_directory(package_name), "launch", "rsp.launch.py")]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": "true",
            "integrated_mode": "true",
        }.items(),
    )
```
*Deutsch:* "Führe die Launch-Datei `rsp.launch.py` aus. Und by the way, gib ihr die Argumente `use_ros2_control:=true` etc. mit auf den Weg."

## 5. Abhängigkeiten und Reihenfolge (Event Handler)
Manchmal darf ein Programm erst gestartet werden, wenn ein anderes fertig ist. 
In deiner Simulation darf der Controller Manager (der Motor-Steuerungen lädt) erst gestartet werden, wenn der Roboter (`spawn_entity`) fertig in die 3D-Welt gesetzt wurde. Ansonsten stürzt der Controller ab, weil er Motoren steuern will, die noch nicht existieren.

Dafür nutzt du **`RegisterEventHandler`** und **`OnProcessExit`**:

```python
    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[diff_drive_spawner],
        )
    )
```
*Deutsch:* "Trag dich in eine Warteliste ein (`RegisterEventHandler`). Wenn das Programm `spawn_entity` fertig/beendet ist (`OnProcessExit`), dann und erst dann führe `diff_drive_spawner` aus (`on_exit`)."

## Zusammenfassung
Deine Hautpdatei `launch_sim.launch.py` tut also folgendes:
1. Sie lädt Argumente (`use_sim_time`, `world`).
2. Sie startet Unter-Launches: `rsp.launch.py` (Roboter-Modell), `joystick.launch.py` (Controller), `ros_gz_sim` (Gazebo 3D Engine).
3. Sie startet Einze/Nodes: `twist_mux` (Mischt Joystick/Navigations-Kommandos), `parameter_bridge` (Übersetzt zwischen ROS und Gazebo).
4. Sie wartet, bis der Roboter in Gazebo gespawnt ist, und startet verzögert (`delayed_...`) alle Motor-Controller (`diff_cont`, `tilt_controller`, etc.).
