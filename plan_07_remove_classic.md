# Remove Gazebo Classic Files and Clean Up References

The user requested the removal of all "classic" files (Gazebo Classic integration). We will delete the files specifically dedicated to Gazebo Classic and update referencing files to remove conditional logic for `use_gazebo_classic`.

## User Review Required

> [IMPORTANT]
> **Code Modification Rule:** In existing files, we will comment out references to Gazebo Classic instead of deleting them.
>
> **File Deletion:** We will delete files that are completely dedicated to Gazebo Classic.

---

## Proposed Changes

### Deletions

#### [DELETE] [ros2_control_gazebo_classic.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/ros2_control_gazebo_classic.xacro)
#### [DELETE] [ros2_control_gazebo_classic.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/nerf_launch_system/description/urdf/ros2_control_gazebo_classic.xacro)
#### [DELETE] [obstacles_classic.world](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/gazebo/worlds/obstacles_classic.world)
#### [DELETE] [test_classic_nerf_teleop_movement.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/tests/test_classic_nerf_teleop_movement.py)
#### [DELETE] [test_classic_launch_args.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/tests/test_classic_launch_args.py)
#### [DELETE] [gz_classic_launch_sim.launch.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/bringup/launch/gz_classic_launch_sim.launch.py)

---

### Clean Up References

#### [MODIFY] [gubot_one_main.urdf.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/gubot_one_main.urdf.xacro)
- Comment out `<xacro:arg name="use_gazebo_classic" ... />`.
- Comment out `<xacro:if value="$(arg use_gazebo_classic)">` block.
- Keep the `<xacro:unless value="$(arg use_gazebo_classic)">` contents without the conditional block.

#### [MODIFY] [nerf_launcher.urdf.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro)
- Comment out references to `use_gazebo_classic`.

#### [MODIFY] [sensor_lidar.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/sensor_lidar.xacro)
- Comment out `use_gazebo_classic` checks and classic sensor definition.

#### [MODIFY] [sensor_camera.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/sensor_camera.xacro)
- Comment out `use_gazebo_classic` checks and classic sensor definition.

#### [MODIFY] [load_urdf.launch.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/launch/load_urdf.launch.py)
- Comment out `use_gazebo_classic` launch configuration and argument.

---

## Verification Plan

### Automated Tests
- Build and run the existing package tests:
  ```bash
  colcon build --packages-select gubot_one nerf_launch_system
  colcon test --packages-select gubot_one nerf_launch_system
  ```
