


colcon build --symlink-install --packages-select nerf_standalone
source install/setup.bash
# Starten
ros2 launch nerf_standalone simulate.launch.py

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
ros2 run nerf_standalone nerf_control_node