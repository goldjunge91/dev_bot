---
trigger: model_decision
---

```markdown
# Simulation Rules & Best Practices

These rules apply to the development and operation of simulations within this workspace.

## System Environment
- **ROS Version**: ROS 2 Humble
- **Gazebo Version**: Gazebo Fortress (Ignition v6)
- **Status**: LTS / Recommended Pairing
- **Documentation**: Use Fortress (Ignition) documentation. Note that Citadel tutorials are mostly compatible, but plugin naming must follow the Ignition v6 convention.

## Commands & Syntax
- **Main Command**: Use `ign gazebo` instead of `gz sim`. 
  - `gz sim` is only available starting from Garden/Harmonic. For Fortress, use `ign`.
- **Introspection**: Use `ign topic -l` or `ign service -l` for debugging.
- **Verbose Mode**: Start with `ign gazebo -v 4 <world_file>.sdf` to see detailed error logs.

## Rendering & Stability (WSL2 / VM)
- **Issue**: The default renderer (OGRE 2) frequently causes `Ogre::UnimplementedException` or crashes in virtualized environments/WSL2.
- **Solution**: Always force **OGRE 1**.
- **CLI Rule**: Append `--render-engine ogre` to every manual start command if operating in WSL2.
- **World Plugin**: If using sensors (camera/lidar), explicitly define the engine in the world file:
  ```xml
  <plugin filename="ignition-gazebo-sensors-system" name="ignition::gazebo::systems::Sensors">
    <render_engine>ogre</render_engine>
  </plugin>

```

## ROS 2 Control (Ignition)

* **Plugin Name**: `ign_ros2_control-system`
* **Class Name**: `gz_ros2_control::GazeboSimROS2ControlPlugin`
* **Hardware Interface**: `gz_ros2_control/GazeboSimSystem`

## Physics & Antigravity (Actors)

* **Physics Plugin**: Ensure `ignition-gazebo-physics-system` is loaded in the `<world>` tag.
* **Antigravity Objects**: For objects that should follow a path without physics interference (no gravity, no collision forces), use the `<actor>` tag.
* Actors are ideal for "floating" elements or scripted test obstacles as they ignore the global gravity vector.



## TF & Transformations

* **World Connection**: Static robots should be connected via a `fixed` joint to the `world` link in the URDF/SDF.
* **Flicker Prevention**: Do not enable `ignition-gazebo-pose-publisher-system` for links already being published by the ROS `robot_state_publisher`. Overlapping TFs will cause visual flickering.
* **Bridge Usage**: Use `ros_gz_bridge` (or `ros_ign_bridge`) for topic synchronization. Prefer using a YAML configuration file for complex bridge setups.

```

```