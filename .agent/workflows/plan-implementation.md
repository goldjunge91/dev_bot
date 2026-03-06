---
description: A structured sequence for planning, developing, and validating ROS2 Humble packages.
---

# ROS2 Humble Plan-Implementation Workflow
**Command**: `/ros2-plan-impl`

## Phase 1: Context & Workspace Setup
- **Source Environment**: Ensure ROS2 Humble is sourced: `source /opt/ros/humble/setup.bash`.
- **Workspace Verification**: Confirm current directory is a ROS2 workspace (contains a `src` folder). If not, offer to create one: `mkdir -p ~/ros2_ws/src && cd ~/ros2_ws`.
- **Dependency Check**: Ensure `rosdep`, `colcon`, and `build-essential` are installed and updated.

## Phase 2: Design & Implementation Plan
- **Task Definition**: Define the specific nodes, topics, services, and actions required.
- **Interface Design**: Identify if standard interfaces (e.g., `std_msgs`, `sensor_msgs`) suffice or if a custom `msg/srv/action` package is needed.
- **Architecture**: Apply the **Single Responsibility Principle**—separate ROS2 communication logic from core application logic.
- **Review**: Present a high-level plan to the user for approval before generating code.

## Phase 3: TDD & Implementation
- **Package Creation**: Generate the package using `ros2 pkg create --build-type [ament_cmake|ament_python] --license Apache-2.0 --node-name [node_name] [package_name]`.
- **Test-First Approach**: 
    - Create a test case in `test/` (C++) or `test/` (Python) that defines the expected behavior.
    - Validate that the test fails before writing implementation code.
- **Code Injection**: 
    - Implement logic based on the approved plan.
    - Follow the rule: Comment out old code first, then insert new code.
- **Launch & Config**: Prefer **XML Launch files** over Python for frontend stability. Use YAML for parameters.

## Phase 4: Build & Resolve
- **Dependency Resolution**: Run `rosdep install -i --from-path src --rosdistro humble -y` to pull in missing system dependencies.
- **Build**: Execute `colcon build --symlink-install --packages-select [package_name]`.
- **Environment Update**: Source the local setup: `source install/local_setup.bash`.

## Phase 5: Verification
- **Automated Testing**: Run `colcon test --packages-select [package_name]` and inspect results with `colcon test-result`.
- **Manual Validation**: Provide the user with the exact `ros2 run` or `ros2 launch` commands to verify the node behavior in a live environment.