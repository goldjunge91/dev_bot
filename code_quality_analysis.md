# Robot Project – Code Quality Analysis

> **Analysed Packages:** `gubot_one` · [nerf_standalone](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone) · `face_tracker` · `diffdrive_arduino`
> **Date:** 2026-03-04
> **Total files analysed:** ~35 source files (Python, C++, headers, CMake, XACRO, YAML)

---

## Summary

| Severity   | Count | Description                                          |
| ---------- | ----- | ---------------------------------------------------- |
| 🔴 Critical | 4     | Bugs / safety issues that can cause runtime failures |
| 🟠 Major    | 8     | Significant code quality / dead code problems        |
| 🟡 Minor    | 12    | Style, consistency, and small improvements           |
| ⚪ Info     | 5     | Notes / observations                                 |

---

## 1 · `face_tracker` Package

### 🔴 Critical Issues

#### 1.1 Unused import `Pose2D` in [detect_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_face.py)
- **File:** [detect_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_face.py#L20)
- **Line 20:** `from geometry_msgs.msg import Pose2D` is imported but **never used**.
- **Impact:** Dead import; no functional bug, but linter noise and wasted namespace.

#### 1.2 `print()` instead of ROS logger
Multiple files use `print()` for output instead of `self.get_logger()`:

| File                                                                                                                      | Line    | Code                                                  |
| ------------------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------- |
| [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py#L73)                 | 73, 108 | `print(e)` in exception handlers                      |
| [detect_ball_3d.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball_3d.py#L84)           | 84      | `print(m.pose.position)` – debug output in production |
| [follow_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/follow_ball.py#L59)                 | 59      | `print(self.target_dist)` – debug output              |
| [fake_face_publisher.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fake_face_publisher.py#L70) | 70      | `print(f"Error: {e}")` in exception handler           |

- **Impact:** `print()` bypasses the ROS2 logging system – no timestamps, no level filtering, no `rqt_console` visibility.

### 🟠 Major Issues

#### 1.3 Empty `pass` block with commented-out log in [fire_at_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py)
- **File:** [fire_at_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py#L119-L121)
- **Lines 119–121:** The `else` branch contains only `pass` and a commented-out logger call.
- **Impact:** This is effectively dead code. The `pass` does nothing and the commented-out log may have been useful for debugging.

#### 1.4 Unused `sys` import in [fake_face_publisher.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fake_face_publisher.py)
- **File:** [fake_face_publisher.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fake_face_publisher.py#L6)
- **Line 6:** `import sys` is imported but never used.

#### 1.5 Mixed [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py) – combines ball-detection AND face-detection utilities
- **File:** [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py)
- Old ball-detection functions (`find_circles`, [apply_search_window](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#94-112), [draw_window2](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#116-128), [convert_rect_perc_to_pixels](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#130-141), [normalise_keypoint](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#143-153), [create_tuning_window](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#155-169), [get_tuning_params](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#171-187), [wait_on_gui](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#189-191), [no_op](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#193-195)) **are still present** alongside the newer face-detection functions ([load_encodings](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#11-20), [find_and_identify_faces](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#22-46), [draw_face_boxes](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#48-75), [normalise_face](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#77-90)).
- The ball-tracking functions like `find_circles` are **referenced** by [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py) so they cannot be removed, but this file is doing double duty.
- **Impact:** Low cohesion. The file mixes two unrelated concerns. Consider splitting into `process_ball.py` and `process_face.py`.

#### 1.6 `find_circles` function is missing from [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py)
- **File:** [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py#L79) calls `proc.find_circles(cv_image, self.tuning_params)` but `find_circles` **is not defined** in [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py).
- **Impact:** 🔴 **`detect_ball` node will crash at runtime** with `AttributeError`. Either the function was removed during face-detection refactoring, or it lives elsewhere. This is a broken dependency.

### 🟡 Minor Issues

#### 1.7 Inconsistent error handling patterns
- [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py) uses bare `print(e)` for CvBridge errors.
- [detect_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_face.py) correctly uses `self.get_logger().error()`.
- [follow_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/follow_face.py) and [fire_at_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py) use proper logging.

#### 1.8 [udp_cam_receiver.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/udp_cam_receiver.py) logs every received frame at INFO level
- **File:** [udp_cam_receiver.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/udp_cam_receiver.py#L50)
- **Line 50:** `self.get_logger().info(f"Frame empfangen von {addr}, PUBLISHED!")` – at 30 FPS this would flood the log.
- **Recommendation:** Change to `self.get_logger().debug()` or use `throttle_duration_sec`.

#### 1.9 [__pycache__](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__) directories in source tree
- Found at: [face_tracker/face_tracker/__pycache__/](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/__pycache__), [face_tracker/test/__pycache__/](file:///home/ros/projects/my_new_robot/src/face_tracker/test/__pycache__)
- **Impact:** Should be in `.gitignore` and removed from version control.

#### 1.10 [register_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/register_face.py) does not spin – runs blocking in [__init__](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball_3d.py#23-41)
- **File:** [register_face.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/register_face.py#L60)
- `self.run_registration()` is called directly from the constructor, which blocks with `cv2.waitKey()` and `time.sleep()`. The main function never calls `rclpy.spin()`.
- **Impact:** Functional but non-standard ROS2 pattern. Works because it's a one-shot registration tool, but callbacks won't be processed.

---

## 2 · [nerf_standalone](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone) Package

### 🟠 Major Issues

#### 2.1 [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py) – Commented-out flywheel publisher
- **File:** [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py#L50-L54)
- **Lines 50–54:** The `flywheel_pub` publisher is commented out. The comments say the firmware FSM now handles flywheels autonomously, which is correct. But this leaves 5 lines of dead commented code.
- **Impact:** Per user rules this is OK (code should be commented out first), but documenting it here for awareness.

#### 2.2 [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py) – `import time` is commented out but still present
- **File:** [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py#L31)
- **Line 31:** `# import time  # Nicht mehr nötig: FSM übernimmt Timing` – dead commented import.

#### 2.3 [setup.py](file:///home/ros/projects/my_new_robot/src/face_tracker/setup.py) has TODO placeholders
- **File:** [setup.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/setup.py#L28-L29)
- **Lines 28–29:** `description="TODO: Package description"` and `license="TODO: License declaration"` are still placeholders.

#### 2.4 [nerf_system.hpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone/nerf_system.hpp) – Unused member variables `tilt_min_rad_` and `tilt_max_rad_`
- **File:** [nerf_system.hpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone/nerf_system.hpp#L210-L211)
- **Lines 210–211:** `tilt_min_rad_` and `tilt_max_rad_` are declared as member variables but **never used** in [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp). The [write()](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp#251-324) method hardcodes `0.01` as the delta threshold and uses `0.05` as the step size, but never references these limits.
- **Impact:** Dead member variables. The tilt limits in [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py) (`self.tilt_min = 5.23`, `self.tilt_max = 6.28`) are used instead.

### 🟡 Minor Issues

#### 2.5 [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp) – Typo / formatting issue in comment
- **File:** [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp#L369)
- **Line 369:** Extra spaces in comment: `// Gebe         Zeiger auf Command-Variable zurück` – should be `// Gebe Zeiger auf Command-Variable zurück`.

#### 2.6 [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp) – `static bool warned` in [write()](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp#251-324) never resets
- **File:** [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp#L255)
- **Line 255:** `static bool warned = false;` – this `static` local means if serial disconnects, reconnects, and disconnects again, the warning won't show a second time because `warned` remains `true` forever.
- **Impact:** Minor logging issue. Consider making it a member variable or resetting it on reconnect.

#### 2.7 [full_system_test.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/full_system_test.py) and [monitor_encoders.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/monitor_encoders.py) – placed in nerf_standalone but test general robot functionality
- [full_system_test.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/full_system_test.py) tests differential drive **and** nerf launcher.
- [monitor_encoders.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/monitor_encoders.py) monitors wheel encoders which belong to `diffdrive_arduino`.
- **Impact:** These scripts belong in `gubot_one` (the main integrating package) rather than [nerf_standalone](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone).

#### 2.8 [__pycache__](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__) directories in source tree
- Found at: [nerf_standalone/nerf_standalone/__pycache__/](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/__pycache__), [nerf_standalone/scripts/__pycache__/](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/__pycache__), [nerf_standalone/test/__pycache__/](file:///home/ros/projects/my_new_robot/src/nerf_standalone/test/__pycache__)

---

## 3 · `gubot_one` Package

### 🔴 Critical Issues

#### 3.1 [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py) – Creates `pub_flywheel` publisher but never uses it
- **File:** [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py#L98-L102)
- **Lines 98–102:** `self.pub_flywheel` publisher is created for `/flywheel_controller/commands` but is **never published to anywhere** in the file.
- **Impact:** Dead code. Since the firmware FSM handles flywheels, this publisher is unnecessary and wastes a ROS2 connection.

### 🟠 Major Issues

#### 3.2 [robot_core_bak.xml](file:///home/ros/projects/my_new_robot/src/gubot_one/description/robot_core_bak.xml) – Backup file in description directory
- **File:** [robot_core_bak.xml](file:///home/ros/projects/my_new_robot/src/gubot_one/description/robot_core_bak.xml)
- This is a full 187-line backup of [robot_core.xacro](file:///home/ros/projects/my_new_robot/src/gubot_one/description/robot_core.xacro). It should not be in the source tree alongside production files.
- **Impact:** Confusing file that could be accidentally included. Should use version control (git) for backups instead.

#### 3.3 [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py) – `sys.exit()` bypasses proper ROS2 shutdown
- **File:** [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py#L172)
- **Line 172:** `sys.exit()` is called on CTRL-C directly from the loop callback, which bypasses [destroy_node()](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/udp_cam_sender.py#70-74) and `rclpy.shutdown()` in the `finally` block.
- **Impact:** Could cause unclean shutdown. Should raise `KeyboardInterrupt` or set a flag instead.

#### 3.4 [__pycache__](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__) directory in scripts
- Found at: [gubot_one/scripts/__pycache__/](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__)

### 🟡 Minor Issues

#### 3.5 CMakeLists.txt uses C++14 standard
- **File:** [CMakeLists.txt](file:///home/ros/projects/my_new_robot/src/gubot_one/CMakeLists.txt#L10)
- **Line 10:** [set(CMAKE_CXX_STANDARD 14)](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/wheel.hpp#27-32) – ROS2 Humble+ recommends C++17. While `gubot_one` has no C++ code, this could cause issues if C++ is added later.

#### 3.6 Shell scripts and DDS config not verified in this analysis
- **Files:** [scripts/apply_bashrc_settings.sh](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/apply_bashrc_settings.sh), [scripts/install_camera_calib.sh](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/install_camera_calib.sh), [scripts/setup_dds_config.sh](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/setup_dds_config.sh), [scripts/start_robot.sh](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/start_robot.sh)
- These were not deeply analysed but are noted as present.

---

## 4 · `diffdrive_arduino` Package

### 🔴 Critical Issues

#### 4.1 [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) – Function defined in header (ODR violation risk)
- **File:** [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#L10-L38)
- **Lines 10–38:** [convert_baud_rate()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#10-39) is a **non-inline free function** defined directly in a header file. If this header were included by more than one [.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp) file, it would cause a linker error (multiple definitions / ODR violation).
- **Impact:** Currently works because only [diffbot_system.cpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp) includes it, but this is fragile. Should be `inline` or moved to a [.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp) file.

#### 4.2 [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) – Uses `std::cout` / `std::cerr` instead of ROS logger
- **File:** [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp)
- **Lines 34, 67, 71, 103:** Uses `std::cout` and `std::cerr` for error and debug output.
- **Impact:** Bypasses ROS2 logging entirely. These messages won't appear in `rqt_console` or log files.

### 🟠 Major Issues

#### 4.3 [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) – Commented-out includes
- **File:** [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#L4-L6)
- **Lines 4, 6:** `// #include <cstring>` and `// #include <cstdlib>` are commented out.

#### 4.4 [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) – No error handling for [read_encoder_values](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#81-92)
- **File:** [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#L81-L91)
- If the serial response is malformed or empty, `response.find(delimiter)` returns `std::string::npos`, `substr()` could throw, or `std::atoi` returns 0 silently.
- **Impact:** Could produce garbage encoder values or crash on malformed data.

#### 4.5 [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) – [send_empty_msg()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#77-80) creates unused local variable
- **File:** [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#L77-L79)
- **Line 78:** `std::string response = send_msg("\r");` – the [response](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py#134-143) is captured but never used.
- **Impact:** Compiler warning potential (unused variable).

#### 4.6 [diffbot_system.cpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp) – Inconsistent namespace qualifier
- **File:** [diffbot_system.cpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#L214)
- **Line 214:** `diffdrive_arduino ::DiffDriveArduinoHardware::write` has an extra space before [::](file:///home/ros/projects/my_new_robot/src/gubot_one/README.md). All other methods use `DiffDriveArduinoHardware::` without namespace prefix (they're already inside the `namespace diffdrive_arduino` block).
- **Impact:** Works but inconsistent style.

#### 4.7 [debug_pins.py](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/debug_pins.py) – Standalone script not installed or integrated
- **File:** [debug_pins.py](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/debug_pins.py)
- This script is not listed in [CMakeLists.txt](file:///home/ros/projects/my_new_robot/src/gubot_one/CMakeLists.txt) for install, and uses `pyserial` directly instead of ROS2 patterns.
- **Impact:** Useful debug tool but lives in an odd location. Not installable via `colcon build`.

### 🟡 Minor Issues

#### 4.8 [wheel.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/wheel.hpp) – Public member variables
- **File:** [wheel.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/wheel.hpp)
- All member variables (`name`, [enc](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#11-20), `cmd`, `pos`, `vel`, `rads_per_count`) are public. This is common in ROS2 hardware interfaces (used as simple data containers), so this is acceptable but noted.

---

## 5 · Cross-Package Issues

### 🟠 5.1 Duplicated Tilt Limits (Magic Numbers)
The tilt servo limits `5.23` rad (DOWN) and `6.28` rad (UP) appear in **4 separate files**:

| File                                                                                                                                     | Location                                                                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py#L76-L77)          | `self.tilt_min = 5.23`, `self.tilt_max = 6.28`                                                                                               |
| [nerf_system.hpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone/nerf_system.hpp#L210-L211) | `tilt_min_rad_ = 5.23`, `tilt_max_rad_ = 6.28` (unused)                                                                                      |
| [nerf_joy.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_joy.py#L63-L64)                                          | `self.tilt_pos = 6.28`, `max(5.23, ...)`, [min(6.28, ...)](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_joy.py#186-191) |
| [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py#L123-L124)                                  | Same hardcoded values                                                                                                                        |

- **Impact:** If the servo limits change, you must update 4 files. These should be ROS2 parameters or defined in a single shared config.

### 🟠 5.2 Duplicated Pusher Pulse Logic
The pusher pulse pattern (set velocity high → wait via timer → reset to 0) is implemented **3 times** with slightly different values:

| File                                                                                                                              | Pulse Speed | Timer Ticks             | Frequency |
| --------------------------------------------------------------------------------------------------------------------------------- | ----------- | ----------------------- | --------- |
| [nerf_joy.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_joy.py#L177-L178)                                 | 20.0        | 5 ticks × 0.05s = 0.25s | 20 Hz     |
| [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py#L158-L159)                           | 20.0        | 5 ticks × 0.1s = 0.5s   | 10 Hz     |
| [nerf_control_node.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/nerf_standalone/nerf_control_node.py#L158-L162) | 10.0        | One-shot timer 0.5s     | N/A       |

- **Impact:** Different pulse durations across control methods. Should use the `/nerf/fire` service consistently.

### 🟡 5.3 Seven [__pycache__](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__) directories across the project
- These should all be cleaned and added to `.gitignore`.
- Found in `face_tracker`, `gubot_one`, [nerf_standalone](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone), and `serial` packages.

### 🟡 5.4 Language mixing in comments/logs
- Code comments and log messages mix German and English inconsistently.
- While not a bug, it reduces readability for international collaborators.
- **Recommendation:** Pick one language (English recommended for ROS2 open-source conventions).

---

## 6 · Useless / Dead Code Summary

| File                                                                                                                                             | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Type                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [detect_face.py:20](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_face.py#L20)                                     | `import Pose2D`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Unused import                                                                                                                                                                          |
| [fake_face_publisher.py:6](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fake_face_publisher.py#L6)                       | `import sys`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Unused import                                                                                                                                                                          |
| [nerf_teleop.py:98-102](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py#L98-L102)                                    | `pub_flywheel` publisher                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Created but never used                                                                                                                                                                 |
| [nerf_system.hpp:210-211](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/include/nerf_standalone/nerf_system.hpp#L210-L211) | `tilt_min_rad_`, `tilt_max_rad_`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Member vars never referenced                                                                                                                                                           |
| [arduino_comms.hpp:78](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#L78)    | [response](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py#134-143) in [send_empty_msg()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#77-80)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Unused variable                                                                                                                                                                        |
| [fire_at_face.py:119-121](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/fire_at_face.py#L119-L121)                        | `else: pass` + commented log                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Dead branch                                                                                                                                                                            |
| [robot_core_bak.xml](file:///home/ros/projects/my_new_robot/src/gubot_one/description/robot_core_bak.xml)                                        | Entire file                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Backup file in source tree                                                                                                                                                             |
| [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#L92-L194)                               | [apply_search_window](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#94-112), [draw_window2](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#116-128), [convert_rect_perc_to_pixels](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#130-141), [normalise_keypoint](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#143-153), [create_tuning_window](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#155-169), [get_tuning_params](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#171-187), [wait_on_gui](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#189-191), [no_op](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py#193-195) | Ball-tracking helpers – possibly still used by [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py) but `find_circles` is **missing** |

---

## 7 · Priority Recommendations

### Immediate (Fix Bugs)
1. **Fix or restore `find_circles` in [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py)** – [detect_ball.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/detect_ball.py) will crash without it
2. **Remove unused `pub_flywheel`** in [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py)
3. **Fix `sys.exit()` in [nerf_teleop.py](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/nerf_teleop.py)** – replace with proper shutdown

### Short-Term (Code Quality)
4. Replace all `print()` calls with `self.get_logger()` (4 files affected)
5. Remove unused imports (`Pose2D`, `sys`)
6. Make [convert_baud_rate()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#10-39) in [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp) `inline`
7. Add error handling to [read_encoder_values()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp#81-92) in [arduino_comms.hpp](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/arduino_comms.hpp)
8. Extract tilt limits to shared ROS2 parameters

### Medium-Term (Architecture)
9. Split [process_image.py](file:///home/ros/projects/my_new_robot/src/face_tracker/face_tracker/process_image.py) into `process_ball.py` + `process_face.py`
10. Move [full_system_test.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/full_system_test.py) and [monitor_encoders.py](file:///home/ros/projects/my_new_robot/src/nerf_standalone/scripts/monitor_encoders.py) to `gubot_one`
11. Unify pusher pulse logic – use `/nerf/fire` service everywhere
12. Clean up [__pycache__](file:///home/ros/projects/my_new_robot/src/gubot_one/scripts/__pycache__) directories and add to `.gitignore`
13. Fill in [setup.py](file:///home/ros/projects/my_new_robot/src/face_tracker/setup.py) TODO descriptions

### Long-Term (Nice to Have)
14. Standardize logging language (English or German, not both)
15. Consider making [Wheel](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/include/diffdrive_arduino/wheel.hpp#21-25) members private with accessors
16. Add `static bool warned` reset in [nerf_system.cpp](file:///home/ros/projects/my_new_robot/src/nerf_standalone/hardware/nerf_system.cpp) on reconnect
