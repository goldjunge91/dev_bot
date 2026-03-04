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

## Getting Started

1. Register a face: `ros2 run face_tracker register_face --ros-args -p person_name:=<name>`
2. Launch: `ros2 launch face_tracker face_tracker.launch.py`