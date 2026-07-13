# Plan 02 — Align `gubot_one` to `rosbot_ros` Reference Workspace

## Goal

Bring `src/gubot_one` into the same Gazebo-simulation quality as `rosbot_ws/src/rosbot_ros` (the `rosbot_xl` mecanum variant).
Focus: **precision parity** — same Gazebo plugin chain, same topic topology, same controller-spawner flow, same EKF setup.

---

## Open Questions

> [!IMPORTANT]
> Please confirm before execution starts:
>
> 1. **Gazebo version**: Current xacro uses `ign_ros2_control-system` (Ignition Fortress). Reference uses `gz_ros2_control/GazeboSimSystem` (Gazebo Garden/Harmonic). Which is installed? Run: `gz sim --version`
> 2. **Joint name prefix**: Reference uses `fl_wheel_joint` / `fr_wheel_joint` / `rl_wheel_joint` / `rr_wheel_joint`. Gubot uses the longer `front_left_wheel_joint` etc. Should we rename to match the reference? This affects URDF + controllers.yaml + hardware firmware.
> 3. **`husarion_gz_worlds`**: The reference `simulation.launch.py` uses `FindPackageShare("husarion_gz_worlds")`. Is this installed? Run: `ros2 pkg list | grep husarion_gz_worlds`

---

## Current State vs. Reference — Gap Analysis

| Area | rosbot_ros (reference) | gubot_one (current) | Gap |
|---|---|---|---|
| **URDF body Z-offset** | `base_to_body_joint` origin Z=`wheel_radius` | origin Z=0.0 | Chassis sits on floor; wheels sink below ground |
| **`base_footprint` link** | Not present | Present, creates extra root-like chain | Can confuse `robot_state_publisher` |
| **ros2_control plugin** | `gz_ros2_control/GazeboSimSystem`, no `position_proportional_gain` | Same plugin but has extra `<param name="position_proportional_gain">20.0</param>` | Extra param not supported by `GazeboSimSystem` |
| **ros2_control sensor name** | `<sensor name="${ns}imu">` | `<sensor name="imu_sensor">` | Must match `controllers.yaml` `sensor_name:` field |
| **Gazebo plugin config path** | Injected via xacro arg `controller_config` | Hard-coded `$(find gubot_one)/controller/config/controllers.yaml` | No namespace/config_dir override possible |
| **Gazebo plugin remappings** | Includes `transition_event` remaps for all controllers | Missing `transition_event` remaps | Controller lifecycle events lost |
| **IMU Gazebo sensor name** | `<sensor name="${ns}imu">` in `gazebo.urdf.xacro` macro | `<sensor name="imu_sensor">` inline in geometry xacro | Mismatch between Gazebo sensor and ros2_control sensor block |
| **simulation.launch.py** | `SetParameter(use_sim_time=True)` + `SetRemap` globally; `husarion_gz_worlds` | No global `SetParameter`/`SetRemap`; inline world path; has `ros_gz_image_bridge` node | Missing global sim-time = broken TF tree in sim |
| **spawn_robot.launch.py** | Pose args (x,y,z,roll,pitch,yaw); `-allow_renaming true`; `PushRosNamespace`; per-robot `gz_bridge` | No pose args; no allow_renaming; no namespace; no per-robot bridge | Robot spawns at origin at Z=0, may sink; no namespace support |
| **controller spawner** | One spawner call with all 3 controllers + `--controller-manager-timeout 20`; `TimerAction(2.0)`; stderr fault monitor | Three separate spawners at 2s/3s/4s stagger; no fault monitor | Race condition possible; silent failures |
| **controllers.yaml sensor_name** | `sensor_name: <namespace>/imu` | `sensor_name: imu_sensor` | Must match ros2_control sensor block name |
| **gz_bridge.yaml scope** | Only `/clock` globally; sensor topics in per-robot bridge | `/clock` + `scan` + `camera/camera_info` all globally | Sensor topics should be per-robot scoped |
| **ekf.launch.py** | No `use_sim_time` arg (relies on global `SetParameter`) | Sets `use_sim_time` per-node | Redundant; can override global setting |
| **package.xml deps** | Declares `robot_localization`, `twist_mux`, `nav2_common`, `gz_ros2_control` etc. | Missing several runtime deps | Build may succeed but runtime will fail |

---

## Proposed Changes — Step by Step

---

### Step 1 — Fix `base_to_body_joint` Z-offset

**File:** `src/gubot_one/description/urdf/gubot_one_geometry.xacro`

**Why:** The reference `body.urdf.xacro` sets `origin xyz="0.0 0.0 ${wheel_radius}"` so that `body_link` is elevated above the ground plane and wheel joints are at ground level (Z=0). The gubot currently sets Z=0.0, which puts the chassis floor on the ground and pushes wheels through the floor.

```diff
 <joint name="base_to_body_joint" type="fixed">
-    <origin xyz="0.0 0.0 0.0" rpy="0.0 0.0 0.0"/>
+    <origin xyz="0.0 0.0 ${wheel_radius}" rpy="0.0 0.0 0.0"/>
```

Also comment out `base_footprint` joint and link (not in reference):
```diff
-<joint name="base_footprint_joint" type="fixed">
-    <parent link="base_link"/>
-    <child link="base_footprint"/>
-    <origin xyz="0 0 0" rpy="0 0 0"/>
-</joint>
-<link name="base_footprint"/>
+<!-- ALT: base_footprint removed — not in rosbot_xl reference, confuses RSP -->
+<!-- <joint name="base_footprint_joint" type="fixed"> ... </joint> -->
+<!-- <link name="base_footprint"/> -->
```

---

### Step 2 — Fix `ros2_control_gazebo_ign_fortress.xacro`

**File:** `src/gubot_one/description/urdf/ros2_control_gazebo_ign_fortress.xacro`

**Sub-change A — Remove unsupported plugin param:**
```diff
 <hardware>
     <plugin>gz_ros2_control/GazeboSimSystem</plugin>
-    <param name="position_proportional_gain">20.0</param>
 </hardware>
```

**Sub-change B — Add `controller_config` xacro arg and use it:**
```diff
+<!-- NEW: controller config path injected by load_urdf.launch.py -->
+<xacro:arg name="controller_config"
+    default="$(find gubot_one)/controller/config/controllers.yaml"/>
 ...
-<parameters>$(find gubot_one)/controller/config/controllers.yaml</parameters>
+<parameters>$(arg controller_config)</parameters>
```

**Sub-change C — Add missing `transition_event` remappings (reference pattern):**
```xml
<!-- ADD after existing remappings: -->
<remapping>differential_drive_controller/transition_event:=_differential_drive_controller/transition_event</remapping>
<remapping>imu_broadcaster/transition_event:=_imu_broadcaster/transition_event</remapping>
<remapping>joint_state_broadcaster/transition_event:=_joint_state_broadcaster/transition_event</remapping>
<remapping>mecanum_drive_controller/transition_event:=_mecanum_drive_controller/transition_event</remapping>
```

---

### Step 3 — Fix IMU sensor name consistency

**Files:** `gubot_one_geometry.xacro` (Gazebo sensor), `ros2_control_gazebo_ign_fortress.xacro` (ros2_control sensor block), `controllers.yaml` (sensor_name param)

All three must use the same string. Current state: geometry uses `imu_sensor`, ros2_control block uses `imu_sensor`, controllers.yaml uses `imu_sensor` → **already consistent within gubot**.

**Action:** Keep `imu_sensor` name. Add a comment in each file linking them:
```xml
<!-- SENSOR NAME: must match ros2_control sensor block name "imu_sensor" -->
<!-- and controllers.yaml imu_broadcaster.sensor_name: imu_sensor -->
```

No functional change — this is a documentation step to prevent future regression.

---

### Step 4 — Update `load_urdf.launch.py` to inject `controller_config`

**File:** `src/gubot_one/description/launch/load_urdf.launch.py`

**Why:** After Step 2 the URDF xacro now accepts `controller_config` as an arg. The launch file must resolve the absolute path at runtime and pass it through.

**Change:** Add `controller_config` arg and inject into xacro Command:
```python
# Add LaunchConfiguration:
controller_config = LaunchConfiguration("controller_config")

# Add to xacro Command list:
" controller_config:=",
controller_config,

# Add DeclareLaunchArgument:
DeclareLaunchArgument(
    "controller_config",
    default_value=PathJoinSubstitution([
        FindPackageShare("gubot_one"), "controller", "config", "controllers.yaml"
    ]),
    description="Absolute path to controllers.yaml passed into URDF xacro.",
),
```

Also add `SetParameter` and `SetRemap` to the returned list (reference pattern from `load_urdf.launch.py`):
```python
SetParameter(name="use_sim_time", value=use_sim_time),
SetRemap("/tf", "tf"),
SetRemap("/tf_static", "tf_static"),
```

---

### Step 5 — Refactor `controller.launch.py` to single spawner with fault monitor

**File:** `src/gubot_one/controller/launch/controller.launch.py`

**Why:** Three staggered spawners create a race condition if the controller_manager starts slowly. The reference uses one spawner with `--controller-manager-timeout 20` that retries internally, plus stderr monitoring for fast failure detection.

**Change:**
```python
# Replace three separate spawners with one:
controllers_spawner = Node(
    package="controller_manager",
    executable="spawner",
    arguments=[
        "mecanum_drive_controller",
        "imu_broadcaster",
        "joint_state_broadcaster",
        "-c", "controller_manager",
        "--controller-manager-timeout", "20",
    ],
)

delayed_controllers_spawner = TimerAction(period=2.0, actions=[controllers_spawner])

def check_if_log_is_fatal(event):
    msg = event.text.decode().lower()
    if ("fatal" in msg or "failed" in msg) and "attempt" not in msg:
        return EmitEvent(event=Shutdown(reason="Spawner failed"))

controllers_monitor = RegisterEventHandler(
    OnProcessIO(
        target_action=controllers_spawner,
        on_stderr=check_if_log_is_fatal,
    )
)
```

Add imports at top:
```python
from launch.actions import EmitEvent, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessIO
from launch.events import Shutdown
```

---

### Step 6 — Fix `simulation.launch.py` global sim-time and remaps

**File:** `src/gubot_one/gazebo/launch/simulation.launch.py`

**Why:** Without `SetParameter(use_sim_time=True)` at the top level, nodes spawned by included launches may use wall-clock time. Without `SetRemap` for `/tf`, the TF tree is broken in namespaced setups.

**Change:** Add before `gz_sim`:
```python
from launch_ros.actions import SetParameter, SetRemap
from launch.actions import SetEnvironmentVariable

# In return LaunchDescription([...]):
SetEnvironmentVariable(name="RCUTILS_COLORIZED_OUTPUT", value="1"),
SetRemap("/diagnostics", "diagnostics"),
SetRemap("/tf", "tf"),
SetRemap("/tf_static", "tf_static"),
SetParameter(name="use_sim_time", value=True),
```

Also remove `ros_gz_image_bridge` node — image bridging will be handled by the per-robot `gubot_bridge.yaml` (Step 8).

**World source:** If `husarion_gz_worlds` is not available keep the current `ros_gz_sim` approach but change `gz_args` to use `gz_log_level: 1` instead of `-v4` for less noise:
```python
launch_arguments={"gz_args": ["-r -v1 ", world], "on_exit_shutdown": "true"}.items(),
```

---

### Step 7 — Fix `spawn_robot.launch.py` pose args and namespace

**File:** `src/gubot_one/gazebo/launch/spawn_robot.launch.py`

**Changes:**
```python
# Add pose arguments:
declare_x_arg   = DeclareLaunchArgument("x",     default_value="0.0",  description="Initial X")
declare_y_arg   = DeclareLaunchArgument("y",     default_value="0.0",  description="Initial Y")
declare_z_arg   = DeclareLaunchArgument("z",     default_value="0.05", description="Initial Z")
declare_roll_arg  = DeclareLaunchArgument("roll",  default_value="0.0")
declare_pitch_arg = DeclareLaunchArgument("pitch", default_value="0.0")
declare_yaw_arg   = DeclareLaunchArgument("yaw",   default_value="0.0")

# Update gz_spawn_entity:
gz_spawn_entity = Node(
    package="ros_gz_sim",
    executable="create",
    arguments=[
        "-name", "gubot_one",
        "-allow_renaming", "true",
        "-topic", "robot_description",
        "-x", x, "-y", y, "-z", z,
        "-R", roll, "-P", pitch, "-Y", yaw,
    ],
    output="screen",
)

# Add per-robot bridge (Step 8 yaml):
gz_robot_bridge = Node(
    package="ros_gz_bridge",
    executable="parameter_bridge",
    name="gubot_gz_bridge",
    parameters=[{"config_file": PathJoinSubstitution([
        FindPackageShare("gubot_one"), "gazebo", "config", "gubot_bridge.yaml"
    ])}],
)
```

---

### Step 8 — Fix `gz_bridge.yaml` scope: clock-only global, sensors per-robot

**Files:**
- `src/gubot_one/gazebo/config/gz_bridge.yaml` — strip to clock-only
- `src/gubot_one/gazebo/config/gubot_bridge.yaml` — **new file**, per-robot sensors

**`gz_bridge.yaml` (global, clock only):**
```yaml
---
  - topic_name: /clock
    ros_type_name: rosgraph_msgs/msg/Clock
    gz_type_name: gz.msgs.Clock
    direction: GZ_TO_ROS
```

**`gubot_bridge.yaml` (new, per-robot):**
```yaml
---
  - topic_name: scan
    ros_type_name: sensor_msgs/msg/LaserScan
    gz_type_name: gz.msgs.LaserScan
    direction: GZ_TO_ROS
  - topic_name: camera/camera_info
    ros_type_name: sensor_msgs/msg/CameraInfo
    gz_type_name: gz.msgs.CameraInfo
    direction: GZ_TO_ROS
  - topic_name: camera/image_raw
    ros_type_name: sensor_msgs/msg/Image
    gz_type_name: gz.msgs.Image
    direction: GZ_TO_ROS
```

---

### Step 9 — Fix `ekf.launch.py` — remove local `use_sim_time` injection

**File:** `src/gubot_one/localization/launch/ekf.launch.py`

**Why:** Global `SetParameter(use_sim_time=True)` from `simulation.launch.py` propagates to all nodes. Setting it again per-node is redundant and can cause subtle issues if the values mismatch.

**Change:**
```python
# Remove:
#   use_sim_time = LaunchConfiguration("use_sim_time", default="false")
#   parameters=[ekf_config, {"use_sim_time": use_sim_time}]
#   DeclareLaunchArgument("use_sim_time", ...)

# Replace with:
robot_localization_node = Node(
    package="robot_localization",
    executable="ekf_node",
    name="ekf_node",
    parameters=[ekf_config],
    remappings=[("/diagnostics", "diagnostics")],
)
```

---

### Step 10 — Update `package.xml` dependencies

**File:** `src/gubot_one/package.xml`

Add missing runtime dependencies:
```xml
<exec_depend>robot_localization</exec_depend>
<exec_depend>twist_mux</exec_depend>
<exec_depend>nav2_common</exec_depend>
<exec_depend>gz_ros2_control</exec_depend>
<exec_depend>ign_ros2_control</exec_depend>
<exec_depend>imu_sensor_broadcaster</exec_depend>
<exec_depend>joint_state_broadcaster</exec_depend>
<exec_depend>mecanum_drive_controller</exec_depend>
<exec_depend>rviz2</exec_depend>
```

---

### Step 11 — Write plan to project root (physical file)

Since this plan lives in the artifact system, also write it as a Markdown file in the project root at:
`/home/ros/projects/my_new_robot_9e34131/plan_02_align_gubot_to_rosbot_reference.md`

---

### Step 12 — Build and smoke-test

```bash
# 1. Build
cd ~/projects/my_new_robot_9e34131
colcon build --packages-select gubot_one --symlink-install

# 2. Validate URDF
ros2 run xacro xacro src/gubot_one/description/urdf/gubot_one_main.urdf.xacro \
  sim_mode:=true use_ros2_control:=true use_nerf_hardware:=false | \
  check_urdf /dev/stdin

# 3. Run pytest suite
colcon test --packages-select gubot_one
colcon test-result --all --verbose

# 4. Launch simulation
ros2 launch gubot_one simulation.launch.py rviz:=true
```

---

### Step 13 — Functional verification

| Check | Command | Expected |
|---|---|---|
| Controllers active | `ros2 control list_controllers` | `mecanum_drive_controller active`, `imu_broadcaster active`, `joint_state_broadcaster active` |
| Odometry topic | `ros2 topic echo /odometry/wheels --once` | Valid `nav_msgs/Odometry` message |
| IMU topic | `ros2 topic echo /imu/data --once` | Valid `sensor_msgs/Imu` message |
| TF tree | `ros2 run tf2_tools view_frames` | Connected tree: `odom → base_link → body_link → [wheel links, imu_link]` |
| Robot pose | RViz | Robot sits on ground plane, chassis correctly elevated |
| Mecanum strafe | `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {y: 0.2}}"` | Robot strafes laterally in Gazebo |

---

## Execution Dependency Order

```
Step 1 (URDF Z-offset + remove base_footprint)
Step 2 (ros2_control xacro: remove param, add controller_config arg, add remaps)
Step 3 (document IMU sensor name consistency — no code change)
  └── Step 4 (load_urdf.launch.py injects controller_config)
        └── Step 5 (controller.launch.py single-spawner + fault monitor)
Step 6 (simulation.launch.py global SetParameter + SetRemap)
  └── Step 7 (spawn_robot.launch.py pose args + per-robot bridge)
        └── Step 8 (gz_bridge.yaml clock-only + new gubot_bridge.yaml)
Step 9 (ekf.launch.py cleanup)
Step 10 (package.xml deps) ← parallel, any time
Step 11 (write plan_02 to project root) ← parallel
Step 12 (build)
Step 13 (verify)
```
