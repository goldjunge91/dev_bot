# Workflow: Mapping & Navigation in the Gazebo Simulation

Step-by-step guide for new users: create a map of the simulated world
(`obstacles.world`) and then navigate on it with Nav2/AMCL.

There are two ways to do the mapping — pick one:

- **Workflow A — Manual (teleop):** you drive the robot with the
  keyboard while SLAM builds the map. Simple, full control.
- **Workflow B — Full Nav2:** the robot drives itself to goals you
  click in RViz while SLAM builds the map. Fewer terminals, but the
  robot only maps where you send it.

Every terminal needs the workspace sourced first:

```bash
cd ~/projects/my_new_robot_9e34131
source install/setup.bash
```

---

## Workflow A — Manual mapping (teleop)

Open 4 Terminals.

### Terminal 1 — Simulation (GUI + RViz)

```bash
ros2 launch gubot_gazebo simulation.launch.py
```

Wait until the robot sits in `obstacles.world` and the controllers are
up (no more spawner output scrolling by).

### Terminal 2 — SLAM

```bash
ros2 launch gubot_navigation slam.launch.py use_sim_time:=true
```

In RViz: **Add → Map**, topic `/map`, and set **Fixed Frame** to `map`.
You'll see the map grow as you drive.

### Terminal 3 — Drive the robot around

```bash
ros2 run gubot_utils teleop_twist_nerf_keyboard.py
```

WASD to drive (publishes `/cmd_vel_joy`, priority 100 in twist_mux).
Drive slowly along the obstacles and cover the area from a few angles —
loop back to where you started so slam_toolbox can close the loop and
clean up the map.

### Terminal 4 — Save the map

When the map in RViz looks complete:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f src/gubot_navigation/maps/obstacles \
  --ros-args -p use_sim_time:=true
```

This writes `obstacles.yaml` + `obstacles.pgm` next to the existing
`test_area` map. Rebuild once so the new files are installed:

```bash
colcon build --symlink-install --packages-select gubot_navigation
```

Then stop SLAM (Ctrl-C in Terminal 2) and teleop (Terminal 3) — see
[After mapping](#after-mapping--navigating-on-the-saved-map).

---

## Workflow B — Full Nav2 mapping (robot drives itself)

### Terminal 1 — Simulation (GUI + RViz)

```bash
ros2 launch gubot_gazebo simulation.launch.py
```

Wait until the robot sits in `obstacles.world` and the controllers are
up.

### Terminal 2 — Nav2 with online SLAM

```bash
ros2 launch gubot_navigation nav2.launch.py slam:=true use_sim_time:=true
```

This starts slam_toolbox **and** the full Nav2 chain — no teleop
terminal needed. In RViz: **Add → Map**, topic `/map`, Fixed Frame
`map`.

Now click **"Nav2 Goal"** in RViz and send the robot to the corners of
the area, one goal at a time. The robot navigates and maps
simultaneously. Send goals so it passes every obstacle and returns to
the start (loop closure).

> If a goal starts aborting with "Extrapolation Error" after ~10 s of
> driving, just re-click the goal — a fresh goal gets a fresh
> timestamp (known Humble quirk).

### Terminal 3 — Save the map

Same as Workflow A:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f src/gubot_navigation/maps/obstacles \
  --ros-args -p use_sim_time:=true
colcon build --symlink-install --packages-select gubot_navigation
```

Then stop Terminal 2 (Ctrl-C) and restart navigation against the saved
map — see next section.

---

## After mapping — navigating on the saved map

Mapping is done once. From now on only **two terminals** are needed —
SLAM and teleop stay off:

### Terminal 1 — Simulation (keep running / start again)

```bash
ros2 launch gubot_gazebo simulation.launch.py
```

### Terminal 2 — Nav2 with AMCL against the saved map

```bash
ros2 launch gubot_navigation nav2.launch.py use_sim_time:=true \
  map:=$(pwd)/src/gubot_navigation/maps/obstacles.yaml
```

(`slam` defaults to `false`, so this runs map_server + AMCL.)

In RViz:

1. Fixed Frame `map`, Map display on `/map`.
2. If the robot did not start at the map origin: **"2D Pose Estimate"**
   — click and drag on the robot's true position/orientation once.
3. **"Nav2 Goal"** — the robot navigates on the saved map.

That's all. Optional extras on top:

| Extra | Command (additional terminal) |
|---|---|
| Sentry mode (face tracking + Nerf) | `ros2 launch gubot_bringup sentry.launch.py use_sim_time:=true map:=$(pwd)/src/gubot_navigation/maps/obstacles.yaml` (replaces Terminal 2) |
| Manual override while Nav2 runs | `ros2 run gubot_utils teleop_twist_nerf_keyboard.py` (priority 100 beats Nav2) |

---

## Tips for a good map

- **Rotate in place** at a few spots — gives the lidar full 360°
  coverage.
- **Drive slowly** past obstacles — the A1 in sim updates at ~10 Hz;
  fast passes leave thin/blurry walls.
- **Cover the borders**: drive close enough to the outer walls that
  they appear as closed lines in the map. Open edges cause harmless
  but noisy `worldToMap failed` spam later during navigation.
- **Close the loop**: end the run where you started; slam_toolbox
  straightens the map on loop closure.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| No map appears in RViz | Fixed Frame not `map`, or SLAM terminal not running with `use_sim_time:=true`. |
| Robot ghost-drifts in RViz | Missed `use_sim_time:=true` in a Nav2/SLAM terminal. |
| `worldToMap failed` spam | Lidar sees obstacles outside the saved map — remap with better border coverage. |
| Goal aborts with Extrapolation Error after ~10 s | Re-click the goal (fresh timestamp). |
| "Entity already exists" on sim start | Zombie processes: `pkill -9 -f "ign gazebo"; pkill -9 rviz2; ros2 daemon stop`. |
