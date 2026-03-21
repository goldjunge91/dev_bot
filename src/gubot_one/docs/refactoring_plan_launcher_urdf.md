# Refactoring-Plan: nerf_launcher.urdf.xacro – Simulation-Optimierung

**Ziel:** Physik-Instabilität beim Tilt-Anschlag beheben, Simulator entlasten, Tilt-Bewegung in launch_sim zuverlässig machen.

---

## Diagnose: Warum kippt der Roboter beim Tilt-Anschlag?

Der `trigger_joint` (Tilt) ist ein `revolute`-Joint mit `lower=5.23` / `upper=6.28` rad.
Wenn er den oberen Anschlag (6.28 rad) erreicht, addiert Ignition Gazebo alle Trägheitsmomente
aller abhängigen Links auf — einschließlich der vier `continuous`-Flywheel/Pusher-Joints
mit `damping=0.0` und `friction=0.0`. Das erzeugt einen unkontrollierten Drehimpuls,
der sich auf den gesamten Roboter überträgt → Kippen.

**Ursachen zusammengefasst:**
1. `flywheel_left_joint` und `flywheel_right_joint` sind `continuous` mit 0 Dämpfung
2. Jedes der 14 Links hat eigene Trägheit → 14 Physikobjekte in Gazebo
3. `motor_left`, `motor_right`, `Turret`, `magazin` sind zwar `fixed`, aber als
   separate Links definiert — Gazebo Classic lumpt diese zusammen, Ignition nicht immer
4. `dart_pusher_joint` ist `continuous` → ebenfalls freier Drehimpuls

---

## Schritt 1: Flywheel-Joints von `continuous` → `fixed`

**Datei:** `src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro`

**Warum:** Die Flywheels haben in der Simulation keinen aktiven Controller mehr
(in `ros2_control.xacro` bereits auskommentiert). Als `continuous`-Joints ohne
Controller treiben sie trotzdem freie Rotation an → Stabilitätsproblem.

**Änderung flywheel_left_joint** (Zeile ~196):
```xml
<!-- ALT: -->
<joint name="flywheel_left_joint" type="continuous">
    ...
    <dynamics damping="0.0" friction="0.0"/>
</joint>

<!-- NEU: -->
<joint name="flywheel_left_joint" type="fixed">
    <origin xyz="0.0 -7.810000000000317e-06 -0.0175"
            rpy="1.5707963267948966 -1.0870161501361781e-16 -2.35430244640625e-21" />
    <parent link="motor_left" />
    <child link="flywheel_left" />
</joint>
```

**Änderung flywheel_right_joint** (analog):
```xml
<joint name="flywheel_right_joint" type="fixed">
    <origin xyz="0.0 -7.800000000000029e-06 -0.0175"
            rpy="1.5707963267948966 -7.224685652388453e-18 -2.3543024464062444e-21" />
    <parent link="motor_right" />
    <child link="flywheel_right" />
</joint>
```

**Visuelle Meshes bleiben unverändert** – nur der Joint-Typ ändert sich.

---

## Schritt 2: Fixed-Links in motor_bracket mergen

**Datei:** `src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro`

**Welche Links werden gemergt:** `motor_left`, `motor_right`, `Turret`, `magazin`
(alle via `type="fixed"` direkt mit `motor_bracket` verbunden).

**Warum:** Obwohl `fixed`-Joints normalerweise vom URDF-Parser zusammengeführt werden,
verarbeitet Ignition Gazebo sie teils als separate Kollisionsobjekte. Durch explizites
Mergen der `<visual>`-Einträge in `motor_bracket` reduzieren wir die Physik-Entities.

**Vorgehen:** Die `<visual>`-Blöcke von `motor_left`, `motor_right`, `Turret` und `magazin`
werden in den `motor_bracket`-Link kopiert. Die separaten `<link>`- und `<joint>`-Definitionen
für diese vier Teile werden entfernt.

**Neuer motor_bracket-Link (Struktur):**
```xml
<link name="motor_bracket">
    <inertial>
        <!-- Gesamtträgheit: Summe aller gemergten Massen -->
        <origin xyz="0.06 0 0" rpy="0 0 0" />
        <mass value="0.5" />  <!-- war 0.1, jetzt Summe 5×0.1 -->
        <inertia ixx="0.005" iyy="0.005" izz="0.005"
                 ixy="0.0" iyz="0.0" ixz="0.0" />
    </inertial>

    <!-- Original motor_bracket visual -->
    <visual name="motor_bracket_visual">
        <origin xyz="0.09803428669398517 -4.3732793080548534e-05 -0.013700000763976723"
                rpy="1.5703501879750486 -1.5707963267948937 0" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/motor_bracket.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: motor_left (transform aus joint motor_bracket_motor_left_fix_motor_bracket) -->
    <visual name="motor_left_visual">
        <!-- origin = Kombination aus Joint-Origin + ursprünglichem visual-Origin -->
        <origin xyz="0.09699999040378247 -4.326999672626883e-05 0.008800001069511083"
                rpy="1.5707963268286462 -1.5707304396707 3.141592653589793" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/motor_left.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: motor_right -->
    <visual name="motor_right_visual">
        <origin xyz="0.09699998532437559 -4.3269996726369024e-05 -0.036199999028498644"
                rpy="1.5707963268286462 -1.5707304396707 3.141592653589793" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/motor_right.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: Turret -->
    <visual name="Turret_visual">
        <origin xyz="0.11710034290805325 0.0007477600039520603 -0.01370000462490558"
                rpy="-1.570796326761147 -1.5707304396707 3.141592653589793" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/Turret.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: magazin -->
    <visual name="magazin_visual">
        <origin xyz="0.014700442685571637 0.0009934500004961037 -0.013700001459844353"
                rpy="-1.570796326761147 -1.5707304396707 3.141592653589793" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/magazin.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: flywheel_left (visual bleibt, Joint wird fixed) -->
    <visual name="flywheel_left_visual">
        <!-- Kombinierter Transform aus joint motor_left_fix + flywheel_left_joint + visual origin -->
        <origin xyz="-0.0631325544432252 0.01313155884148008 -0.0631300993428637"
                rpy="-1.570165432787083 0.7853321767598774 -3.1411465441724866" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/flywheel_left.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- Gemergt: flywheel_right (analog) -->
    <visual name="flywheel_right_visual">
        <origin xyz="-0.01550858803514851 0.013120498025483157 -0.08792554788989197"
                rpy="-1.568228080674074 1.3961969502773832 -3.139063424976714" />
        <geometry>
            <mesh filename="file://$(find nerf_launch_system)/description/meshes/flywheel_right.stl"
                  scale="0.001 0.001 0.001" />
        </geometry>
    </visual>

    <!-- KEINE <collision>-Tags – motor_bracket hat bisher keine Collision, das bleibt so -->
</link>
```

**Zu löschende Links:** `motor_left`, `motor_right`, `Turret`, `magazin`, `flywheel_left`, `flywheel_right`

**Zu löschende Joints:**
- `motor_bracket_motor_left_fix_motor_bracket`
- `motor_bracket_motor_right_fix_motor_bracket`
- `motor_bracket_torret_on_motor_bracket`
- `motor_bracket_magazin_fix_motor_bracket`
- `flywheel_left_joint`
- `flywheel_right_joint`

---

## Schritt 3: Trägheitsmomente korrigieren

**Datei:** `src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro`

Nach dem Mergen hat `motor_bracket` die Masse von 7 ehemaligen Links übernommen
(motor_bracket + motor_left + motor_right + Turret + magazin + flywheel_left + flywheel_right).

```xml
<!-- motor_bracket inertial – NEU -->
<inertial>
    <origin xyz="0.06 0 0" rpy="0 0 0" />
    <mass value="0.7" />   <!-- 7 × 0.1 kg -->
    <inertia ixx="0.007" iyy="0.007" izz="0.007"
             ixy="0.0" iyz="0.0" ixz="0.0" />
</inertial>
```

**Hinweis:** Die Trägheitswerte sind Schätzungen. Für exakte Physik müsste man
STL-Volumen × Dichte berechnen. Für Simulation reichen diese Werte.

---

## Schritt 4: dart_pusher_joint dämpfen

**Datei:** `src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro`

Der `dart_pusher_joint` ist `continuous` mit 0 Dämpfung. Das verursacht beim
Tilt-Anschlag ebenfalls freien Drehimpuls. Dämpfung hinzufügen:

```xml
<!-- ALT: -->
<dynamics damping="0.0" friction="0.0"/>

<!-- NEU: -->
<dynamics damping="0.5" friction="0.2"/>
```

---

## Schritt 5: Tilt-Controller in launch_sim aktivieren

**Datei:** `src/gubot_one/launch/launch_sim.launch.py`

Das eigentliche Problem warum Tilt nicht funktioniert: In `my_controllers.yaml`
heißt der Controller `tilt_controller`, aber er wird in `launch_sim.launch.py`
nicht gespawnt. Die `ros2_control.xacro` von gubot_one hat den `trigger_joint`
im IgnitionSystem, aber kein Spawner startet ihn.

```python
# In launch_sim.launch.py – NEU hinzufügen:
tilt_controller_spawner = Node(
    package="controller_manager",
    executable="spawner",
    arguments=["tilt_controller"],
    output="screen",
    condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
)
delayed_tilt = RegisterEventHandler(
    event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[tilt_controller_spawner])
)
```

Und in `LaunchDescription([...])` ergänzen:
```python
delayed_tilt,
```

**Gleichzeitig:** In `my_controllers.yaml` prüfen ob `tilt_controller` korrekt
auf `trigger_joint` zeigt (aktuell korrekt, kein Fix nötig).

---

## Schritt 6: gz_bridge.yaml – Tilt-Command-Topic ergänzen

**Datei:** `src/gubot_one/config/gz_bridge.yaml`

Der Tilt-Controller publiziert auf `/tilt_controller/commands` (Float64MultiArray).
Dieses Topic fehlt noch im Bridge:

```yaml
# Tilt (Trigger Joint) ROS → GZ
- ros_topic_name: "tilt_controller/commands"
  gz_topic_name: "tilt_controller/commands"
  ros_type_name: "std_msgs/msg/Float64MultiArray"
  gz_type_name: "gz.msgs.Double_V"
  direction: "ROS_TO_GZ"
```

---

## Zusammenfassung: Was ändert sich wo

| # | Datei | Änderung | Effekt |
|---|---|---|---|
| 1 | `nerf_launcher.urdf.xacro` | flywheel Joints: `continuous` → `fixed` | kein freier Drehimpuls mehr |
| 2 | `nerf_launcher.urdf.xacro` | motor_left/right/Turret/magazin/flywheel in motor_bracket mergen | 9 Physics-Objekte weniger |
| 3 | `nerf_launcher.urdf.xacro` | motor_bracket Masse/Trägheit auf 0.7kg anpassen | realistischere Physik |
| 4 | `nerf_launcher.urdf.xacro` | dart_pusher_joint damping 0→0.5 | stabiler beim Anschlag |
| 5 | `launch_sim.launch.py` | `tilt_controller` Spawner ergänzen | Tilt funktioniert in Sim |
| 6 | `gz_bridge.yaml` | `tilt_controller/commands` Topic ergänzen | ROS→GZ Bridge vollständig |

## Wichtig: Reihenfolge der Umsetzung

1. Schritt 1 zuerst (schnellste Wirkung, geringes Risiko)
2. Schritt 4 + 5 + 6 parallel (launch_sim + bridge, kein URDF-Touch)
3. Schritt 2 + 3 zuletzt (größte URDF-Änderung, sorgfältig testen)

Nach jeder Änderung: `colcon build --packages-select nerf_launch_system gubot_one --symlink-install`

## Test nach Umsetzung

```bash
# Tilt manuell testen:
ros2 topic pub /tilt_controller/commands std_msgs/msg/Float64MultiArray \
  "data: [5.23]" --once   # unterer Anschlag → kein Kippen?

ros2 topic pub /tilt_controller/commands std_msgs/msg/Float64MultiArray \
  "data: [6.28]" --once   # oberer Anschlag → kein Kippen mehr?
```

## Was wir NICHT ändern

- `bottom_plate` – hat bereits eine sinnvolle Box-Collision, bleibt
- `Servo_dart_pusher` + `pusher_servo_part` – aktive Controller-Chain, bleibt
- `Nerf-Dart-Launcher_Servo-MG-v1` + `Servoarm-v1` – rein visuell, fixed, stört nicht
- `system_arming_joint` – aktiver Controller, bleibt
- `trigger_joint` – das ist der Tilt-Joint selbst, bleibt revolute
