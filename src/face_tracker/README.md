# face_tracker

Face detection, recognition, and tracking package for the Gubot One robot with Nerf launcher integration.

Uses the `face_recognition` library for face detection and identification against registered face profiles.

## Nodes

- **detect_face** – Detects and identifies faces in camera images, publishes `Detection2DArray` on `/face_detections`
- **follow_face** – Steers the robot to follow a detected face using `cmd_vel` and tilt servo commands
- **fire_at_face** – Triggers the Nerf launcher `/nerf/fire` service when a face is centered and close enough
- **register_face** – Interactive tool to register new face profiles (captures samples via camera)
- **udp_cam_sender** – Streams camera video via UDP for offloading processing to a remote PC
- **udp_cam_receiver** – Receives UDP camera stream and publishes as ROS2 Image topic
- **fake_face_publisher** – Publishes simulated face detections for testing without a camera

## Launch Files

- `face_tracker.launch.py` – Main face tracking pipeline (detect + follow + fire)
- `face_tracker_sim.launch.py` – Face tracking configured for Gazebo simulation
- `face_tracker_udp.launch.py` – Face tracking with UDP camera stream for remote processing

### `face_tracker.launch.py` arguments

| Argument | Default | Meaning |
|---|---|---|
| `params_file` | `config/face_tracker_params.yaml` | Parameter file for all face_tracker nodes. |
| `detect_only` | `false` | Only start `detect_face` (no `follow_face`, no `fire_at_face`). |
| `follow_only` | `false` | Only start `follow_face` (no `detect_face`). |
| `use_sim_time` | `false` | Enable sim time (Gazebo). |
| `image_topic` | `/camera/image_raw` | Input image topic for `detect_face`. |
| `cmd_vel_topic` | `/cmd_vel_tracker` | Output topic for drive commands (twist_mux input, priority 20). |
| `target_person` | `""` (empty) | Person to track/fire at (empty = any face). |
| `allow_search` | `false` | Rotate the robot to search when no face is visible. |

### `face_tracker_sim.launch.py` arguments

| Argument | Default | Meaning |
|---|---|---|
| `detect_only` | `false` | Detection only, robot does not move. |

Wraps `face_tracker.launch.py` with `image_topic:=/camera/image_raw`
(images come from Gazebo via `ros_gz_bridge`, no camera driver started).

### `face_tracker_udp.launch.py` arguments

| Argument | Default | Meaning |
|---|---|---|
| `detect_only` | `false` | Detection only, robot does not move. |
| `follow_only` | `false` | Only start `follow_face`. |

Runs `udp_cam_receiver` on the remote PC and feeds the received stream
into the detection pipeline (`udp_cam_sender` runs on the robot).

## Getting Started

1. Register a face: `ros2 run face_tracker register_face --ros-args -p person_name:=<name>`
2. Launch: `ros2 launch face_tracker face_tracker.launch.py`