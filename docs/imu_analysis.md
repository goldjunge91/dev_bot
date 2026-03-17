# IMU Implementation Analysis: Husarion vs. Local

This document compares the IMU implementation in the Husarion Rosbot repositories with our current local implementation.

## Husarion Implementation Overview

Husarion uses a highly modular and asynchronous approach centered around **micro-ROS**.

### 1. Firmware Level
- **Sensor:** Typically uses the BNO055 (or similar) which provides high-level fused data.
- **Communication:** Uses micro-ROS directly on the STM32. It publishes `sensor_msgs/Imu` messages to a ROS topic (e.g., `~/imu`) independently of the motor control loop.
- **Modularity:** The IMU logic is encapsulated in `lib/imu` with a clear `ImuInterface`.

### 2. Hardware Interface (ROS 2 Control)
- **Type:** Implements `hardware_interface::SensorInterface` as a standalone plugin (`RosbotImuSensor`).
- **Data Acquisition:** Instead of reading from a serial port directly, it **subscribes** to the ROS topic published by the firmware. 
- **Synchronization:** The [read()](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#200-233) method simply copies the latest cached message from the subscriber into the [state_interfaces](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#103-141).
- **Activation:** It includes a "waiting for message" timeout during the [on_activate](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#178-191) phase to ensure the sensor is alive before the controller starts.

---

## Local Implementation Comparison

Our current implementation is more "monolithic" and uses a traditional Serial stream.

| Feature | Husarion | Local (Current) |
| :--- | :--- | :--- |
| **Modularity** | Separate `SensorInterface` plugin | Integrated into `SystemInterface` |
| **Communication** | micro-ROS Topic (Subscriber) | Serial Stream (Raw Strings) |
| **Data Types** | Accel, Gyro, **Orientation** | Accel, Gyro (Orientation is 0.0) |
| **Fusion** | On-sensor (BNO055) | None (Missing Filter) |
| **Activation** | Check with Timeout | No check |

---

## What is Missing / What We Should Change

Based on the Husarion implementation, there are several key areas where we can improve:

### 1. Orientation Fusion (Critical Gap)
The local firmware reads raw acceleration and angular velocity but does not compute orientation. The ROS 2 hardware interface exports orientation interfaces, but they are not populated.
- **Action:** Implement an AHRS filter (e.g., Madgwick or EKF) either in the firmware (using the ICM-20948's DMP if possible) or in the hardware interface/a separate ROS node.

### 2. Modularity & Decoupling
Husarion separates the IMU into its own `hardware_interface`. 
- **Benefit:** If the IMU fails or is disconnected, the motor control (SystemInterface) could potentially still function. It also makes it easier to replace the IMU with a different model (e.g., BNO055 vs ICM-20948) without touching the motor code.
- **Action:** Consider splitting `DiffDriveArduinoHardware` into a `System` component (motors) and a [Sensor](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/firmware/ROSArduinoBridge/imu_driver.ino#37-38) component (IMU).

### 3. Robustness (Health Checks)
Husarion's [on_activate](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#178-191) check for incoming messages is a best practice.
- **Action:** Add a check in [on_activate](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#178-191) to ensure the 'i' command returns valid data before allowing the system to fully activate.

### 4. Communication Strategy
While Husarion uses micro-ROS topics, our Serial stream is more efficient for "dumb" microcontrollers (like Pico/Arduino) that don't run a full micro-ROS stack easily. However, we should ensure the Serial reading is non-blocking or handled at a high enough frequency to not lag the control loop.

---

---

## Specific Takeaways We Can Adopt

Here are concrete elements from the Husarion implementation that we can "take" to improve our robot:

### 1. Robust Activation (Health Check)
**Husarion Pattern:** The [on_activate](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#178-191) method doesn't just start; it waits (with a timeout) for the first valid IMU message to arrive.
- **Why:** It prevents the robot from moving if the IMU is flatlining or disconnected, which is a major safety feature for navigation.
- **Implementation:** Add a similar loop in `DiffDriveArduinoHardware::on_activate` that sends the 'i' command and waits for a non-zero response.

### 2. Configurable Communication Parameters
**Husarion Pattern:** They define `connection_timeout_ms` and `connection_check_period_ms` as hardware parameters in the XACRO.
- **Why:** Allows tuning the startup sensitivity without recompiling the C++ code.
- **Implementation:** Add these parameters to our `ros2_control` configuration and use them in the [on_activate](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#178-191) loop.

### 3. Coordinate System Standard (REP 103)
**Husarion Pattern:** They use `axis_config` and `axis_sign` to ensure the IMU output matches the robot's physical orientation.
- **Why:** Eases the integration with `robot_localization` (EKF).
- **Implementation:** We should verify if our ICM-20948 data needs remapping to ensure X is forward, Y is left, and Z is up.

### 4. Firmware Interface Abstraction
**Husarion Pattern:** A virtual `ImuInterface` class that decouples the sensor-specific driver (BNO055) from the micro-ROS logic.
- **Why:** Makes it trivial to swap sensors (e.g., if we upgrade from ICM-20948 to BNO055).
- **Implementation:** Refactor our `ROSArduinoBridge` to use a similar interface for `imu_driver`.

### 5. Standardized State Interfaces
**Husarion Pattern:** Uses standard ROS 2 naming for interfaces (`linear_acceleration.x`, etc.) inside the `hardware_interface`.
- **Why:** Better compatibility with the `imu_sensor_broadcaster`.
- **Implementation:** We should ensure our [export_state_interfaces](file:///home/ros/projects/my_new_robot/src/diffdrive_arduino/hardware/diffbot_system.cpp#103-141) naming is 100% compliant with the standard broadcaster.
