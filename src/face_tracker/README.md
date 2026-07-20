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

## Tests

```bash
colcon test --packages-select face_tracker
```

Die reine Logik ist aus den Nodes in testbare Module extrahiert
(verhaltensidentisch): `targeting.py` (Ziel-Auswahl + Feuerbedingungen),
`follow_logic.py` (Tiefpass + Verfolgungs-Kommando),
`detection_mapping.py` (Pixel → normierte Bounding-Box).

| Datei | Ebene | Inhalt |
|---|---|---|
| `test/test_targeting.py` | Pure Unit | `select_target`-Fälle, `evaluate_fire` (strikte Thresholds, Cooldown, Kamera-Offset) |
| `test/test_follow_logic.py` | Pure Unit | Tiefpass, Lenk-Vorzeichen, Vorwärts-Stopp, Tilt-Integrator + Klemmung |
| `test/test_detection_mapping.py` | Pure Unit | bbox-Normierung, Scores |
| `test/test_process_image.py` | Unit (gemockt) | Encodings-I/O, argmin-Match, unknown-Fälle, Box-Zeichnung |
| `test/test_fire_at_face_rclpy.py` | rclpy-Integration | Echter Graph mit Mock-`/nerf/fire`-Server: feuert genau 1×, Cooldown blockt, `target_person` wird respektiert |
| `test/test_detect_face_rclpy.py` | rclpy-Integration | Bild-Callback mit CvBridge-Images, Publisher abgefangen |

**Out of scope** (bewusst untestet): `register_face.py` (interaktive
GUI), `udp_cam_sender.py` / `udp_cam_receiver.py` (Socket-I/O).
