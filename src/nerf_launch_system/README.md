


colcon build --symlink-install --packages-select nerf_launch_system
source install/setup.bash
# Starten
ros2 launch nerf_launch_system simulate.launch.py

1. Status prüfen
Zeigt dir die aktuelle Position und Geschwindigkeit aller Gelenke an.

ros2 topic echo /joint_states --once
1. Topics auflisten
Zeigt alle verfügbaren Topics an.


ros2 topic list

3. Steuerung (Sicher!)
Jetzt nutzt du die neuen "User-Friendly" Topics:

Tilt (0.0 = Unten, 0.5 = Mitte, 1.0 = Oben):

bash
# Mitte (Horizontal)
ros2 topic pub --once /nerf/tilt std_msgs/msg/Float64MultiArray "{data: [0.5]}"
# Ganz nach oben
ros2 topic pub --once /nerf/tilt std_msgs/msg/Float64MultiArray "{data: [1.0]}"


# Gehe zur Position 5.5
ros2 topic pub --once /trigger_controller/commands std_msgs/msg/Float64MultiArray "{data: [5.5]}"

# Teste Horizontal
ros2 topic pub --once /trigger_controller/commands std_msgs/msg/Float64MultiArray "{data: [5.75]}"


B. Flywheels (Geschwindigkeit)
Hier steuerst du die Drehzahl beider Räder. Da der Controller 2 Gelenke hat (left und right), musst du zwei Werte senden!

# Beide an (Geschwindigkeit 100)
ros2 topic pub /flywheel_controller/commands std_msgs/msg/Float64MultiArray "{data: [100.0, 100.0]}"

# Beide aus
ros2 topic pub /flywheel_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0, 0.0]}"

C. Pusher (Geschwindigkeit)
Das ist der Continuous Servo. Du steuerst die Geschwindigkeit.

# Pushen (drehen)
ros2 topic pub --once /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [10.0]}"

# Stoppen
ros2 topic pub --once /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0]}"

💡 Tipp für klemmende Simulation
Falls Gazebo mal "hängt" oder du Fehler wie "Address already in use" bekommst, hilft der "große Hammer" vor dem Neustart:

pkill -f gazebo && pkill -f gzserver && pkill -f gzclient && pkill -f ros2


Feuern (Automatische Sequenz): Startet Flywheels -> Pusht Dart -> Stoppt alles.

ros2 service call /nerf/fire std_srvs/srv/Trigger
ros2 run nerf_launch_system nerf_control_node

Now try launching again in a fresh terminal:
```bash
cd /home/ros/projects/my_new_robot
source install/setup.bash
ros2 launch nerf_launch_system simulate.launch.py
Pro tip: If you ever see this issue again, run:
```
```bash
pkill -9 -f robot_state_publisher
ros2 daemon stop
pkill -9 -f robot_state_publisher
ros2 daemon stop
cd /home/ros/projects/my_new_robot
source install/setup.bash
ros2 launch gubot_one launch_sim.launch.py
```
Die Simulation startet nun standardmäßig mit der leeren Welt:
ros2 launch nerf_launch_system simulate.launch.py



ros2 launch nerf_launch_system simulate.launch.py world:=$(ros2 pkg prefix nerf_launch_system)/share/nerf_launch_system/worlds/obstacles.world


<!-- 

""""# Robot Nerf Launcher

ROS 2 package for controlling a Nerf dart launcher via Arduino Pro Micro.

## Architecture

```
ROS 2 Topics → nerf_launcher_node.py → USB Serial → Arduino Pro Micro → ESCs + Servos
```

## Installation

```bash
# Build
colcon build --packages-select nerf_dart_launcher

# Source
source install/setup.bash
```

## Usage

```bash
# Start the node
ros2 launch nerf_dart_launcher nerf_launcher.launch.py

# With custom serial port
ros2 launch nerf_dart_launcher nerf_launcher.launch.py serial_port:=/dev/ttyACM1
```

## ROS Topics

| Topic              | Type      | Description                  |
| ------------------ | --------- | ---------------------------- |
| `cmd/arm`          | `Bool`    | `true`=ARM, `false`=DISARM   |
| `cmd/fire`         | `Bool`    | `true`=execute shot sequence |
| `cmd/tilt`         | `Float32` | Tilt angle 0-180°            |
| `cmd/power`        | `Float32` | Shot power 0-80%             |
| `status/armed`     | `Bool`    | Current armed state          |
| `status/connected` | `Bool`    | Serial connection status     |

## Parameters

| Parameter     | Default        | Description         |
| ------------- | -------------- | ------------------- |
| `serial_port` | `/dev/ttyACM0` | Arduino serial port |
| `baud_rate`   | `115200`       | Serial baud rate    |

## Firmware

Arduino firmware is in the `firmware/` directory. See [firmware/README.md](firmware/README.md).

## Quick Test

```bash
ros2 topic pub --once /nerf_launcher/cmd/arm std_msgs/msg/Bool "data: true"
ros2 topic pub --once /nerf_launcher/cmd/tilt std_msgs/msg/Float32 "data: 45.0"
ros2 topic pub --once /nerf_launcher/cmd/fire std_msgs/msg/Bool "data: true"
ros2 topic pub --once /nerf_launcher/cmd/arm std_msgs/msg/Bool "data: false"
```
"""" -->