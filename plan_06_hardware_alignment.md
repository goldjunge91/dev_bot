# Align Real Hardware Mecanum Robot Configuration and Fix Launch/Test Files

We need to align the real hardware ROS 2 Control configuration, launch files, and test files with the simulation setup. The robot simulation currently uses renamed joints (`fl/fr/rl/rr_wheel_joint`) and a unified controllers configuration path (`controller/config/controllers.yaml`), but the real hardware description (`ros2_control_hardware.xacro`), classic simulation launch (`gz_classic_launch_sim.launch.py`), bringup launch script (`launch_robot.launch.py`), and test suite (`test_launch_robot.py`) still use the old joint names (`front_left_wheel_joint`, etc.), outdated controller names (`mecanum_cont`), or refer to deleted config files.

## User Review Required

> [IMPORTANT]
> **Code Modification Rule:** All changes must comment out old code first rather than deleting it. Unused code will remain commented out in the files.
>
> **Joint Renaming:** The joint names on the real hardware (in the hardware interface configuration) will be changed from `front_left_wheel_joint` to `fl_wheel_joint` to match `gubot_one_geometry.xacro` and `controllers.yaml`.
>
> **Test Synchronization:** We will update the test suite assertions in `test_launch_robot.py` to expect `mecanum_drive_controller` instead of the old `mecanum_cont` controller.

---

## Proposed Changes

### Gubot One URDF & Launch Config

#### [MODIFY] [ros2_control_hardware.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/ros2_control_hardware.xacro)
Rename joints inside the `<ros2_control>` block to match `fl_wheel_joint` / `fr_wheel_joint` / `rl_wheel_joint` / `rr_wheel_joint` instead of the old long names. Update the hardware parameters `front_left_wheel_name` etc. accordingly. Keep the old lines commented out.

#### [MODIFY] [ros2_control_gazebo_classic.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/description/urdf/ros2_control_gazebo_classic.xacro)
Rename joints to match the new naming convention (`fl_wheel_joint` etc.). Keep the old lines commented out.

#### [MODIFY] [launch_robot.launch.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/bringup/launch/launch_robot.launch.py)
- Change `config/my_controllers.yaml` reference to `controller/config/controllers.yaml`.
- Rename `mecanum_cont` controller spawner and arguments to `mecanum_drive_controller`.
- Update twist_mux remapping to `/mecanum_drive_controller/cmd_vel_unstamped`.
- Spawn `imu_broadcaster` sequentially (after `joint_state_broadcaster`) since it is configured in `controllers.yaml` and exported by real hardware.
- Keep all old code commented out.

#### [MODIFY] [gz_classic_launch_sim.launch.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/bringup/launch/gz_classic_launch_sim.launch.py)
- Rename `mecanum_cont` to `mecanum_drive_controller` on lines 81 and 127.
- Keep all old code commented out.

---

### Mecanum Pico Config

#### [MODIFY] [mecanum_controllers.yaml](file:///home/ros/projects/my_new_robot_9e34131/src/mecanum_pico/bringup/config/mecanum_controllers.yaml)
Rename joints from `front_left_wheel_joint` to `fl_wheel_joint` etc. to keep config aligned across packages. Keep old entries commented out.

#### [MODIFY] [mecanum_pico.ros2_control.xacro](file:///home/ros/projects/my_new_robot_9e34131/src/mecanum_pico/description/ros2_control/mecanum_pico.ros2_control.xacro)
Rename joints to `${prefix}fl_wheel_joint` etc. and update wheel parameter defaults. Keep old entries commented out.

---

### Gubot One Test Configuration

#### [MODIFY] [test_launch_robot.py](file:///home/ros/projects/my_new_robot_9e34131/src/gubot_one/tests/test_launch_robot.py)
- Update check on line 18, 19, 67, 70, 77, 78, 92, 101, 102 to expect `mecanum_drive_controller` instead of `mecanum_cont`.
- Keep old assert/documentation lines commented out.

---

## Verification Plan

### Automated Tests
- Build and run the existing package tests:
  ```bash
  colcon build --packages-select gubot_one mecanum_pico
  colcon test --packages-select gubot_one mecanum_pico
  ```
- Verify XML schema using `ament_xmllint` on URDF files.

### Manual Verification
- Render the URDF in non-simulation mode using `xacro` and check that the resulting XML has correct joint names and parameters:
  ```bash
  ros2 run xacro xacro src/gubot_one/description/urdf/gubot_one_main.urdf.xacro sim_mode:=false
  ```
- Dry-run the hardware bringup (mocking or listing the parameters) to ensure no syntax errors:
  ```bash
  ros2 launch gubot_one launch_robot.launch.py
  ```
