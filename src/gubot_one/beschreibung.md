# Projektbeschreibung: Gubot One

Diese Datei bietet eine detaillierte Übersicht über die Konfigurations-, Beschreibungs-, Skript- und Startdateien des `gubot_one` Pakets.

---

## 1. Konfigurationsdateien (.yaml)

| Datei                             | Aufgabe / Funktion                                                                                         | Verwendung in / durch                            |
| :-------------------------------- | :--------------------------------------------------------------------------------------------------------- | :----------------------------------------------- |
| `ball_tracker_params_robot.yaml`  | Enthält HSV-Filterwerte und Regelparameter für das Ball-Tracking auf dem echten Roboter.                   | `ball_tracker.launch.py`                         |
| `ball_tracker_params_sim.yaml`    | Enthält HSV-Filterwerte und Regelparameter, die speziell für die Gazebo-Simulation optimiert sind.         | `ball_tracker.launch.py`                         |
| `empty.yaml`                      | Eine leere Platzhalterdatei, um die Ordnerstruktur in Git konsistent zu halten.                            | N/A                                              |
| `gaz_ros2_ctl_use_sim.yaml`       | Setzt den `use_sim_time` Parameter für den Controller Manager auf `true`.                                  | `gz_classic_launch_sim.launch.py`                |
| `gazebo_params.yaml`              | Konfigurierte Gazebo-spezifische Parameter, wie z.B. die `publish_rate`.                                   | `launch_sim.launch.py`                           |
| `joystick.yaml`                   | Definiert Achsen- und Button-Mappings sowie Geschwindigkeits-Skalierungen für den Joystick/Gamepad.        | `joystick.launch.py`                             |
| `mapper_params_online_async.yaml` | Konfiguration für `slam_toolbox` zur Erstellung von Karten (SLAM) im asynchronen Modus.                    | `online_async_launch.py`                         |
| `my_controllers.yaml`             | Zentrale Konfiguration aller `ros2_control` Controller (DiffDrive, JointBroadcaster, Nerf-Controller).     | `launch_robot.launch.py`, `launch_sim.launch.py` |
| `nav2_params.yaml`                | Umfassende Konfiguration für den Navigation Stack (AMCL, Planner, Controller, Costmaps).                   | `navigation_launch.py`, `localization_launch.py` |
| `twist_mux.yaml`                  | Konfiguriert die Prioritäten für verschiedene Geschwindigkeitsquellen (Joystick vs. Tracker vs. Keyboard). | `launch_robot.launch.py`, `launch_sim.launch.py` |

---

## 2. Roboter-Beschreibung (.xacro / .xml)

| Datei                           | Aufgabe / Funktion                                                                                                                               | Verwendung in / durch                               |
| :------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------- |
| `robot.urdf.xacro`              | Die Haupt-Xacro-Datei, die alle anderen Komponenten (Core, Sensoren, Control) zusammenfügt.                                                      | `rsp.launch.py` (Zentrale Einstiegsdatei)           |
| `robot_core.xacro`              | Definiert die physische Struktur des Roboters (Chassis, Räder, Trägheitsmomente, Farben).                                                        | `robot.urdf.xacro`                                  |
| `camera.xacro`                  | Fügt dem Roboter-Modell eine einfache Kamera hinzu und konfiguriert das Gazebo-Sensor-Plugin.                                                    | `robot.urdf.xacro`                                  |
| `depth_camera.xacro`            | (Optional/Deaktiviert) Definition einer Tiefenkamera für das Modell.                                                                             | `robot.urdf.xacro` (auskommentiert)                 |
| `face.xacro`                    | Fügt ein schmückendes "Gesicht" (Visual) am Chassis des Roboters hinzu.                                                                          | `robot.urdf.xacro`                                  |
| `ros2_control.xacro`            | Konfiguriert die `ros2_control` Schnittstellen für **echte Hardware** (Arduino/Pico) und **Gazebo Sim (Ignition)**.                              | `robot.urdf.xacro`                                  |
| `gz_classic_ros2_control.xacro` | Konfiguriert die `ros2_control` Schnittstellen speziell für **Gazebo Classic**.                                                                  | `robot.urdf.xacro` (wenn `use_gazebo_classic=true`) |
| `gazebo_control.xacro`          | **Veraltet**: Altes Gazebo-Plugin ohne `ros2_control`. Wird nicht mehr benötigt, da Hardware und Sim nun einheitlich über `ros2_control` laufen. | `robot.urdf.xacro` (nur Backup-Option)              |
|                                 |
| `lidar.xacro`                   | Definiert den LIDAR-Sensor (RPLidar) und dessen Integration in Gazebo.                                                                           | `robot.urdf.xacro`                                  |
| `nerf_launcher.xacro`           | Physische Beschreibung und Gelenke des Nerf-Launchers (Tilt, Flywheels, Pusher).                                                                 | `robot.urdf.xacro`                                  |
| `inertial_macros.xacro`         | Enthält Hilfs-Makros zur Berechnung von Trägheitsmomenten (Box, Zylinder, Kugel).                                                                | `robot_core.xacro`                                  |
| `robot_core_bak.xml`            | Eine Sicherungskopie der ursprünglichen Roboterstruktur.                                                                                         | N/A (Sicherung)                                     |

---

## 3. Python-Skripte (.py)

| Datei                 | Aufgabe / Funktion                                                                                   | Verwendung in / durch             |
| :-------------------- | :--------------------------------------------------------------------------------------------------- | :-------------------------------- |
| `nerf_joy.py`         | Konvertiert Joystick-Buttons direkt in Befehle für die Nerf-Controller (Arming, Firing).             | `joystick.launch.py`              |
| `nerf_teleop.py`      | Ein interaktives Tastatur-Teleop-Skript zur manuellen Steuerung von Basis und Launcher.              | Manuelle Ausführung im Terminal   |
| `sim_nerf_service.py` | Stellt ein Service-Interface bereit, um den Nerf-Launcher in der Simulation wie Hardware zu steuern. | `launch_sim.launch.py` (Optional) |

---

## 4. Launch-Dateien (.py)

| Datei                             | Aufgabe / Funktion                                                                          | Verwendung in / durch                            |
| :-------------------------------- | :------------------------------------------------------------------------------------------ | :----------------------------------------------- |
| `rsp.launch.py`                   | **Robot State Publisher**: Verarbeitet Xacro zu URDF und publiziert TF-Transformationen.    | Basis für fast alle anderen Launch-Dateien       |
| `launch_robot.launch.py`          | Startet die Hardware-Basis des echten Roboters inklusive Controller und Hardware-Interface. | `launch_all_real.launch.py`                      |
| `launch_all_real.launch.py`       | **Haupt-Startdatei**: Startet Roboter-Basis, Kamera und Lidar koordiniert.                  | Manuelle Ausführung (Echtbetrieb)                |
| `launch_sim.launch.py`            | Startet die Simulation in **Gazebo Sim (Ignition)** mit allen Controllern und Bridge.       | Manuelle Ausführung (Simulation)                 |
| `gz_classic_launch_sim.launch.py` | Startet die Simulation in **Gazebo Classic**.                                               | Manuelle Ausführung (Simulation alt)             |
| `joystick.launch.py`              | Startet die Knoten für die Controller-Eingabe und die Konvertierung zu Bewegungsbefehlen.   | `launch_robot.launch.py`, `launch_sim.launch.py` |
| `ball_tracker.launch.py`          | Startet das Image-Processing und die Verfolgung eines farbigen Balls.                       | Manuelle Ausführung / Experimente                |
| `camera.launch.py`                | Startet den generischen v4l2 Kamera-Treiber für USB-Kameras.                                | Einzeltest der Kamera                            |
| `real_camera.launch.py`           | Spezifische Kamera-Konfiguration für den echten Roboter (Optimierte FPS/Auflösung).         | `launch_all_real.launch.py`                      |
| `rplidar.launch.py`               | Treiber-Launch für den RPLidar Laserscanner am USB-Port des Raspberry Pi.                   | `launch_all_real.launch.py`                      |
| `online_async_launch.py`          | Startet das asynchrone SLAM-System zur Kartenerstellung während der Fahrt.                  | Manuelle Ausführung (Mapping)                    |
| `localization_launch.py`          | Startet AMCL und den Map-Server zur Lokalisierung in einer bestehenden Karte.               | Navigations-Stack                                |
| `navigation_launch.py`            | Startet den Nav2 Stack (Planner, Controller, BT) für autonome Fahrten.                      | Komplettes Navigations-Setup                     |
