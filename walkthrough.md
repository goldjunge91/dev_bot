# Implementation Walkthrough: Mecanum Drive Upgrade

This document outlines the changes made to integrate the 4-wheel `mecanum_pico` hardware package into the `gubot_one` ROS 2 description, while fully preserving the old differential drive code through `xacro:if` conditionals.

## 1. URDF Geometry Updates
- We added a new `drive_type` argument to [gubot_one_main.urdf.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/gubot_one_main.urdf.xacro) (default: `mecanum`).
- In [gubot_one_geometry.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/gubot_one_geometry.xacro), we wrapped the `caster_wheel` definitions inside `<xacro:if value="${'$(arg drive_type)' == 'diffdrive'}">`.
- We kept the existing `left_wheel` and `right_wheel` to act as the front wheels.
- We added two new wheels (`rear_left_wheel`, `rear_right_wheel`) mapped to `X = -wheel_offset_x = -0.226`, matching the defined chassis boundaries. We wrapped these in `<xacro:if value="${'$(arg drive_type)' == 'mecanum'}">`.

## 2. ROS 2 Control Adjustments
- Modified [ros2_control_hardware.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/ros2_control_hardware.xacro), wrapping the existing `DiffDriveArduino` plugin block in `<xacro:if value="${'$(arg drive_type)' == 'diffdrive'}">`.
- Added a parallel `<xacro:if value="${'$(arg drive_type)' == 'mecanum'}">` block describing the `mecanum_pico/MecanumPicoHardware` plugin, exporting velocity commands and position/velocity state interfaces for all 4 wheel joints.
- Applied identical `drive_type` conditionals inside [ros2_control_gazebo_classic.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/ros2_control_gazebo_classic.xacro) and [ros2_control_gazebo_ign_fortress.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/ros2_control_gazebo_ign_fortress.xacro) to toggle between the 2-joint diff drive setup and the 4-joint mecanum setup.

## 3. Controller Manager Configuration
- Copied the existing [my_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/my_controllers.yaml) to create [mecanum_my_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/mecanum_my_controllers.yaml).
- Replaced the `diff_drive_controller` definition with a `mecanum_drive_controller/MecanumDriveController` node.
- Defined all four command joints (`front_left_wheel_joint`, `front_right_wheel_joint`, `rear_left_wheel_joint`, `rear_right_wheel_joint`).
- Transferred `wheels_radius: 0.033` and calculated the Mecanum kinematics variable `sum_of_robot_center_projection_on_X_Y_axis: 0.2615` based on the front axle location (`wheel_offset_x / 2 + wheel_offset_y`).
- Included `<xacro:if>` blocks inside the Gazebo plugins (in the `ros2_control_gazebo_*.xacro` files) to dynamically load either [my_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/my_controllers.yaml) or [mecanum_my_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/mecanum_my_controllers.yaml) based on the `drive_type`.
- **Naming Convention**: Standardized all mecanum wheel joints to use the `front_left/front_right` prefix for maximum compatibility with generic controllers.

## 4. Compile and Run Checks
- Executed `colcon build --packages-select gubot_one` to verify the modified launch and config files install correctly.
- Verified both `<xacro:if>` configurations expanded cleanly without syntax errors mathematically using `xacro src/gubot_one/description/gubot_one_main.urdf.xacro drive_type:=mecanum` and `drive_type:=diffdrive`.

## 5. Teleoperation Updates for Mecanum
To take full advantage of the omnidirectional mecanum wheels, teleoperation nodes were updated to send lateral velocity commands (`linear.y`):
- **Cleanliness**: Removed residual "Pub Twist" logging from the teleop script to keep the terminal output clean during operation (requires a rebuild to update the `install` folder).
- **Keyboard ([teleop_twist_nerf_keyboard.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/scripts/teleop_twist_nerf_keyboard.py))**: Added `Shift+A` (A) and `Shift+D` (D) to strafe left and right respectively.
- **Joystick ([joystick.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/joystick.yaml))**: Configured the `teleop_twist_joy` node to use `axis_linear.y` mapped to `Axis 0` (Left Stick Left/Right) for strafing, and moved `axis_angular.yaw` to `Axis 3` (Right Stick Left/Right) to support modern drone/FPS style movement.

## 6. Controller & Launch File Integration
- **Twist Routing**: Updated [launch_sim.launch.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/launch/launch_sim.launch.py) to route `/cmd_vel_out` from `twist_mux` to `/mecanum_cont/cmd_vel_unstamped` instead of `/diff_cont/cmd_vel_unstamped`.
- **Controller Spawner**: Replaced the hardcoded `diff_cont` spawner in the launch file with `mecanum_cont`.
- **Velocity Message Syntax**: Added `use_stamped_vel: false` to [mecanum_my_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/config/mecanum_my_controllers.yaml). This is very crucial, as ROS 2 Humble controllers default to expecting `TwistStamped` messages, but our `twist_mux` and teleop scripts publish raw `Twist` messages.

## 7. Troubleshooting Movement
If the robot still doesn't move:
1. Check if `/cmd_vel_joy` is alive: `ros2 topic echo /cmd_vel_joy`
2. Check if `twist_mux` outputs: `ros2 topic echo /mecanum_cont/cmd_vel`
3. Verify controller state: `ros2 control list_controllers`
4. Check if joints are moving in Rviz: `ros2 run rviz2 rviz2` (Add RobotModel and check TF).
