# Simulation Rules & Best Practices

Diese Regeln gelten für die Entwicklung und den Betrieb der Simulation in diesem Workspace.

## System-Umgebung
- **ROS Version**: ROS 2 Humble
- **Gazebo Version**: Gazebo Fortress (Ignition v6)
- **Status**: Recommended / LTS

## Gazebo Syntax & Kommandos
- **Befehl**: Verwende `ign gazebo` anstelle von `gz sim`.
  - `gz sim` ist erst ab Version Garden/Harmonic verfügbar. In Fortress dient [gz](file:///opt/ros/humble/share/ros_gz_sim/launch/gz_sim.launch.py#87-164) nur zur Introspektion (Topics, Modelle).
- **Beispiel**: `ign gazebo shapes.sdf`

## Rendering & Stabilität (Wichtig!)
- **Problem**: Der Standard-Renderer (OGRE 2) verursacht oft `Ogre::UnimplementedException` in virtuellen Umgebungen oder unter WSL2.
- **Lösung**: Erzwinge immer **OGRE 1**.
- **Regel**: Hänge bei jedem manuellen Start `--render-engine ogre` an.
- **Launch-Files**: In Python Launch-Files muss das Argument `--render-engine ogre` fest in die `gz_args` integriert sein.

## ROS 2 Control (Ignition)
- **Plugin Name**: `ign_ros2_control-system`
- **Class Name**: `gz_ros2_control::GazeboSimROS2ControlPlugin`
- **Hardware Interface**: `gz_ros2_control/GazeboSimSystem`

## TF & Transformationen
- **Welt-Verbindung**: Roboter sollten über ein `fixed` joint im URDF mit dem [world](file:///home/ros/projects/my_new_robot/src/nerf_launch_system/worlds/empty.world) link verbunden sein.
- **Vermeidung von Flackern**: `ignition-gazebo-pose-publisher-system` sollte mit Vorsicht genossen werden. Wenn der `robot_state_publisher` TFs sendet, darf das Gazebo-Plugin nicht dieselben TFs senden (Flickering).
