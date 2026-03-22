# Mecanum Drive Hardware Interface — Implementation Plan
### Refactoring `diffdrive_arduino` → `mecanum_pico` for Raspberry Pi Pico + ROS 2 Humble

---

> **Guiding Principles**
> - **KISS**: Every layer (serial protocol, C++ HW interface, Pico firmware) solves one problem. No abstraction until it hurts.
> - **TDD**: Write the test first. Red → Green → Refactor. Hardware-in-the-loop (HIL) tests close each sprint.
> - **Incrementality**: Each sprint produces a runnable, testable artifact. No sprint ends in "compile but untested" state.

---

## Architecture Overview

```
[ Nav2 / Teleop ]
      │  geometry_msgs/TwistStamped (cmd_vel)
      ▼
[ mecanum_drive_controller ]  ← ros2_controllers
      │  velocity commands: FL, FR, RL, RR  (rad/s)
      ▼
[ MecanumPicoHardware ]       ← THIS PACKAGE  (SystemInterface)
      │  Serial UART (USB CDC)
      │  Protocol: "m <fl> <fr> <rl> <rr>\n"   (write)
      │             "e <fl> <fr> <rl> <rr>\n"   (read)
      ▼
[ Raspberry Pi Pico ]         ← Firmware (C/MicroPython)
      │  PWM → Motor Driver × 4
      ▼
[ 4 × Mecanum Wheels + Encoders ]
```

---

## Package Naming & Scope Decision

| Old | New |
|-----|-----|
| `diffdrive_arduino` | `mecanum_pico` |
| `DiffDriveArduino` (C++ class) | `MecanumPicoHardware` |
| `arduino_comms.hpp` | `pico_comms.hpp` |
| `Wheel` struct (2 instances) | `Wheel` struct (4 instances: fl, fr, rl, rr) |
| `diff_drive_controller` | `mecanum_drive_controller` |

---

## Sprint 0 — Repository Setup & Baseline Audit

### Objective
Fork, rename, and audit the existing codebase. Establish a clean baseline before touching any logic.

### Sub-Tasks

1. **Fork & rename the package**
   ```bash
   # In your dev_bot workspace:
   cp -r src/diffdrive_arduino src/mecanum_pico
   # Update package.xml: name, description, maintainer
   # Update CMakeLists.txt: project(mecanum_pico)
   # Rename class files (optional at this stage; keep old names with TODOs)
   ```

2. **Inventory every `2-wheel` assumption** — open each file and add a `// TODO(mecanum):` comment anywhere left/right is hardcoded:
   - `include/diffdrive_arduino/diffdrive_arduino.hpp` → `Wheel left_wheel_`, `Wheel right_wheel_`
   - `src/diffdrive_arduino.cpp` → `export_state_interfaces`, `export_command_interfaces`, `read`, `write`
   - `include/diffdrive_arduino/arduino_comms.hpp` → `sendEmptyMsg`, `readEncoderValues`, `setMotorValues`
   - `config/my_controllers.yaml` → controller type and joint names

3. **Tag the baseline** in git:
   ```bash
   git add -A && git commit -m "chore: fork diffdrive_arduino as mecanum_pico baseline"
   git tag v0.0.0-baseline
   ```

4. **Create the test scaffolding** (empty but buildable):
   ```
   mecanum_pico/
   ├── test/
   │   ├── CMakeLists_test.cmake   # included by main CMakeLists
   │   ├── test_wheel.cpp          # Sprint 1 target
   │   ├── test_pico_comms.cpp     # Sprint 2 target
   │   └── test_hardware_interface.cpp  # Sprint 3 target
   ```

5. **Add `ament_cmake_gtest`** to `package.xml` and `CMakeLists.txt` test section:
   ```cmake
   find_package(ament_cmake_gtest REQUIRED)
   ament_add_gtest(test_wheel test/test_wheel.cpp)
   target_link_libraries(test_wheel mecanum_pico)
   ```

### TDD Strategy
- Run `colcon test --packages-select mecanum_pico` → **zero tests, zero failures** (empty suite). This confirms the test infrastructure compiles.
- Check `colcon test-result --verbose` for a clean output.

### Documentation Requirements
- `README.md`: Add a "Development" section with a "Running Tests" subsection.
- Each source file: Add a `// MIGRATION STATUS: [BASELINE | IN PROGRESS | COMPLETE]` banner at the top.

---

## Sprint 1 — Data Model: Extend `Wheel` to 4 Wheels

### Objective
Refactor the internal data model from 2 wheels (left/right) to 4 independent wheels (front_left, front_right, rear_left, rear_right). No serial communication changes yet — only in-memory structures.

### Sub-Tasks

1. **Write failing tests first** (`test/test_wheel.cpp`):
   ```cpp
   #include <gtest/gtest.h>
   #include "mecanum_pico/wheel.hpp"

   // Test: Wheel stores name correctly
   TEST(WheelTest, NameIsSetOnConstruction) {
     Wheel w("front_left_wheel_joint", 20);
     EXPECT_EQ(w.name, "front_left_wheel_joint");
   }

   // Test: encoder ticks to radians conversion
   TEST(WheelTest, CalcEncAngleCorrect) {
     Wheel w("test", 20);  // 20 ticks/rev
     w.enc = 10;
     w.calcEncAngle();
     EXPECT_NEAR(w.angle, M_PI, 1e-9);  // 10/20 * 2π = π
   }

   // Test: 4-wheel struct holds all wheels independently
   TEST(FourWheelTest, WheelsAreIndependent) {
     Wheel fl("fl", 20), fr("fr", 20), rl("rl", 20), rr("rr", 20);
     fl.cmd = 1.0; fr.cmd = 2.0; rl.cmd = 3.0; rr.cmd = 4.0;
     EXPECT_DOUBLE_EQ(fl.cmd, 1.0);
     EXPECT_DOUBLE_EQ(rr.cmd, 4.0);
   }
   ```

2. **Rename `wheel.hpp`** internal struct fields; ensure it is wheel-count-agnostic (it already is — `Wheel` is a single-wheel struct, which is correct).

3. **Update `mecanum_pico.hpp`**: Replace 2-wheel members with 4:
   ```cpp
   // Before:
   Wheel left_wheel_;
   Wheel right_wheel_;

   // After:
   Wheel wheel_fl_;  // front_left
   Wheel wheel_fr_;  // front_right
   Wheel wheel_rl_;  // rear_left
   Wheel wheel_rr_;  // rear_right
   ```

4. **Update `on_init()`** in `mecanum_pico.cpp` to read 4 joint names from URDF parameters:
   ```cpp
   // In on_init():
   cfg_.front_left_wheel_name  = info_.hardware_parameters.at("front_left_wheel_name");
   cfg_.front_right_wheel_name = info_.hardware_parameters.at("front_right_wheel_name");
   cfg_.rear_left_wheel_name   = info_.hardware_parameters.at("rear_left_wheel_name");
   cfg_.rear_right_wheel_name  = info_.hardware_parameters.at("rear_right_wheel_name");
   ```

5. **Update `Config` struct** in `mecanum_pico.hpp`:
   ```cpp
   struct Config {
     std::string front_left_wheel_name  = "front_left_wheel_joint";
     std::string front_right_wheel_name = "front_right_wheel_joint";
     std::string rear_left_wheel_name   = "rear_left_wheel_joint";
     std::string rear_right_wheel_name  = "rear_right_wheel_joint";
     float loop_rate   = 30.0;
     std::string device = "/dev/ttyACM0";
     int baud_rate     = 115200;
     int timeout_ms    = 1000;
     int enc_counts_per_rev = 1440;
   };
   ```

6. **Update `export_state_interfaces()`**:
   ```cpp
   hardware_interface::CallbackReturn MecanumPicoHardware::export_state_interfaces(
     std::vector<hardware_interface::StateInterface> & state_interfaces)
   {
     // Pattern repeated for all 4 wheels:
     for (auto * w : {&wheel_fl_, &wheel_fr_, &wheel_rl_, &wheel_rr_}) {
       state_interfaces.emplace_back(
         hardware_interface::StateInterface(w->name, hardware_interface::HW_IF_VELOCITY, &w->vel));
       state_interfaces.emplace_back(
         hardware_interface::StateInterface(w->name, hardware_interface::HW_IF_POSITION, &w->angle));
     }
     return hardware_interface::CallbackReturn::SUCCESS;
   }
   ```

7. **Update `export_command_interfaces()`**:
   ```cpp
   hardware_interface::CallbackReturn MecanumPicoHardware::export_command_interfaces(
     std::vector<hardware_interface::CommandInterface> & command_interfaces)
   {
     for (auto * w : {&wheel_fl_, &wheel_fr_, &wheel_rl_, &wheel_rr_}) {
       command_interfaces.emplace_back(
         hardware_interface::CommandInterface(w->name, hardware_interface::HW_IF_VELOCITY, &w->cmd));
     }
     return hardware_interface::CallbackReturn::SUCCESS;
   }
   ```

### TDD Strategy
- Run `colcon test --packages-select mecanum_pico` → **3 tests pass** (WheelTest suite).
- The package must still compile even though `read()`/`write()` call stubs that don't yet send 4 values.

### Documentation Requirements
- `wheel.hpp`: Add Doxygen block explaining `enc`, `cmd`, `vel`, `angle` fields.
- `mecanum_pico.hpp`: Comment each `Wheel` member with its physical position (e.g., `// Front-left wheel, positive = forward-left`).

---

## Sprint 2 — Serial Protocol: Extend to 4-Wheel Commands & Feedback

### Objective
Redesign the serial communication layer (`pico_comms.hpp`) to send 4 velocity commands and receive 4 encoder tick counts in a single transaction.

### Sub-Tasks

1. **Define the wire protocol** (document before coding):

   | Direction | Frame format | Example |
   |-----------|-------------|---------|
   | Host → Pico (command) | `m <fl> <fr> <rl> <rr>\n` | `m 100 -100 100 -100\n` |
   | Pico → Host (feedback) | `e <fl> <fr> <rl> <rr>\n` | `e 1234 -1230 1231 -1228\n` |
   | Host → Pico (reset encoders) | `r\n` | `r\n` |
   | Pico → Host (ack) | `OK\n` | `OK\n` |

   > Values are signed 32-bit integers representing encoder **tick counts** (cumulative, not delta). The host is responsible for converting ticks to radians and computing velocity via differentiation over `dt`.

2. **Write failing tests first** (`test/test_pico_comms.cpp`) — use a loopback serial port or a mock:
   ```cpp
   // Mock: replace ArduinoComms with a testable subclass that records sent strings
   class MockPicoComms : public PicoComms {
   public:
     std::string last_sent;
     void sendRaw(const std::string & msg) override { last_sent = msg; }
   };

   TEST(PicoCommsTest, SetMotorValuesFormatsCorrectly) {
     MockPicoComms comms;
     comms.setMotorValues(100, -100, 100, -100);
     EXPECT_EQ(comms.last_sent, "m 100 -100 100 -100\n");
   }

   TEST(PicoCommsTest, ParseEncoderResponseValid) {
     PicoComms comms;
     int fl, fr, rl, rr;
     bool ok = comms.parseEncoderResponse("e 10 -10 10 -10\n", fl, fr, rl, rr);
     EXPECT_TRUE(ok);
     EXPECT_EQ(fl, 10); EXPECT_EQ(fr, -10);
   }

   TEST(PicoCommsTest, ParseEncoderResponseMalformed) {
     PicoComms comms;
     int fl, fr, rl, rr;
     bool ok = comms.parseEncoderResponse("e 10 -10\n", fl, fr, rl, rr);  // only 2 values
     EXPECT_FALSE(ok);
   }
   ```

3. **Refactor `arduino_comms.hpp` → `pico_comms.hpp`**:
   ```cpp
   // pico_comms.hpp

   void setMotorValues(int fl, int fr, int rl, int rr) {
     std::stringstream ss;
     ss << "m " << fl << " " << fr << " " << rl << " " << rr << "\n";
     sendRaw(ss.str());
   }

   bool readEncoderValues(int & fl, int & fr, int & rl, int & rr) {
     sendRaw("e\n");
     std::string response = readLine();  // blocks until '\n' or timeout
     return parseEncoderResponse(response, fl, fr, rl, rr);
   }

   bool parseEncoderResponse(const std::string & line, int & fl, int & fr, int & rl, int & rr) {
     // Expects "e <fl> <fr> <rl> <rr>\n"
     char prefix;
     int parsed = sscanf(line.c_str(), "%c %d %d %d %d", &prefix, &fl, &fr, &rl, &rr);
     return (parsed == 5 && prefix == 'e');
   }
   ```

4. **Update `read()` in `mecanum_pico.cpp`**:
   ```cpp
   hardware_interface::return_type MecanumPicoHardware::read(
     const rclcpp::Time & time, const rclcpp::Duration & period)
   {
     int fl_enc, fr_enc, rl_enc, rr_enc;
     if (!comms_.readEncoderValues(fl_enc, fr_enc, rl_enc, rr_enc)) {
       RCLCPP_ERROR(rclcpp::get_logger("MecanumPicoHardware"), "Failed to read encoder values");
       return hardware_interface::return_type::ERROR;
     }

     double dt = period.seconds();
     double radians_per_tick = (2.0 * M_PI) / cfg_.enc_counts_per_rev;

     auto update_wheel = [&](Wheel & w, int new_enc) {
       double delta_enc = static_cast<double>(new_enc - w.enc);
       w.enc    = new_enc;
       w.angle += delta_enc * radians_per_tick;
       w.vel    = (dt > 0.0) ? (delta_enc * radians_per_tick / dt) : 0.0;
     };

     update_wheel(wheel_fl_, fl_enc);
     update_wheel(wheel_fr_, fr_enc);
     update_wheel(wheel_rl_, rl_enc);
     update_wheel(wheel_rr_, rr_enc);

     return hardware_interface::return_type::OK;
   }
   ```

5. **Update `write()` in `mecanum_pico.cpp`**:
   ```cpp
   hardware_interface::return_type MecanumPicoHardware::write(
     const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
   {
     auto to_ticks_per_loop = [&](double rad_per_s) -> int {
       double ticks_per_s = rad_per_s * cfg_.enc_counts_per_rev / (2.0 * M_PI);
       return static_cast<int>(ticks_per_s / cfg_.loop_rate);
     };

     comms_.setMotorValues(
       to_ticks_per_loop(wheel_fl_.cmd),
       to_ticks_per_loop(wheel_fr_.cmd),
       to_ticks_per_loop(wheel_rl_.cmd),
       to_ticks_per_loop(wheel_rr_.cmd)
     );
     return hardware_interface::return_type::OK;
   }
   ```

   > **Note**: The Pico firmware is responsible for interpreting these as per-loop tick targets and running its own PID. Sending `rad/s` directly (as floats in the protocol) is an alternative discussed in Sprint 5.

### TDD Strategy
- `colcon test` → **PicoCommsTest suite passes** (all 3 tests, no hardware required).
- Manual smoke test using a Python serial loopback script on `/dev/pts/X` (using `socat` to create a virtual port pair).
  ```bash
  socat -d -d PTY,raw,echo=0 PTY,raw,echo=0
  # Then point the node at /dev/pts/X and run a minimal test launch
  ```

### Documentation Requirements
- `pico_comms.hpp`: Full Doxygen for `setMotorValues` and `readEncoderValues` — include units, value ranges, error behavior.
- `README.md`: Add a "Serial Protocol" section with the full frame format table from this sprint.

---

## Sprint 3 — Hardware Interface: Full Integration & URDF Update

### Objective
Complete the `MecanumPicoHardware` plugin, update the URDF/xacro and controllers config, and verify the full ROS 2 control chain loads without errors.

### Sub-Tasks

1. **Update `ros2_control.xacro`** — declare 4 joints:
   ```xml
   <ros2_control name="MecanumPicoHardware" type="system">
     <hardware>
       <plugin>mecanum_pico/MecanumPicoHardware</plugin>
       <param name="front_left_wheel_name">front_left_wheel_joint</param>
       <param name="front_right_wheel_name">front_right_wheel_joint</param>
       <param name="rear_left_wheel_name">rear_left_wheel_joint</param>
       <param name="rear_right_wheel_name">rear_right_wheel_joint</param>
       <param name="loop_rate">30</param>
       <param name="device">/dev/ttyACM0</param>
       <param name="baud_rate">115200</param>
       <param name="timeout_ms">1000</param>
       <param name="enc_counts_per_rev">1440</param>
     </hardware>

     <joint name="front_left_wheel_joint">
       <command_interface name="velocity">
         <param name="min">-10</param>
         <param name="max">10</param>
       </command_interface>
       <state_interface name="velocity"/>
       <state_interface name="position"/>
     </joint>
     <!-- Repeat for front_right, rear_left, rear_right -->
   </ros2_control>
   ```

2. **Update `controllers.yaml`**:
   ```yaml
   controller_manager:
     ros__parameters:
       update_rate: 30

       mecanum_drive_controller:
         type: mecanum_drive_controller/MecanumDriveController

       joint_state_broadcaster:
         type: joint_state_broadcaster/JointStateBroadcaster

   mecanum_drive_controller:
     ros__parameters:
       front_left_wheel_command_joint_name:  front_left_wheel_joint
       front_right_wheel_command_joint_name: front_right_wheel_joint
       rear_right_wheel_command_joint_name:  rear_right_wheel_joint
       rear_left_wheel_command_joint_name:   rear_left_wheel_joint
       kinematics:
         base_frame_offset:
           x: 0.0
           y: 0.0
           theta: 0.0
         wheels_radius: 0.05             # metres — MEASURE YOUR WHEEL
         sum_of_robot_center_projection_on_X_Y_axis: 0.30  # lx + ly — MEASURE YOUR CHASSIS
       base_frame_id: base_link
       odom_frame_id: odom
       enable_odom_tf: true
       reference_timeout: 0.5
   ```

3. **Register the plugin** in `mecanum_pico.xml` (hardware plugin descriptor):
   ```xml
   <library path="mecanum_pico">
     <class name="mecanum_pico/MecanumPicoHardware"
            type="mecanum_pico::MecanumPicoHardware"
            base_class_type="hardware_interface::SystemInterface">
       <description>
         Mecanum drive hardware interface for Raspberry Pi Pico via USB-CDC serial.
       </description>
     </class>
   </library>
   ```

4. **Register the plugin in `CMakeLists.txt`**:
   ```cmake
   pluginlib_export_plugin_description_file(hardware_interface mecanum_pico.xml)
   ```

5. **Update `package.xml`** — add `mecanum_drive_controller` as an exec dependency:
   ```xml
   <exec_depend>mecanum_drive_controller</exec_depend>
   ```

6. **Write a hardware interface load test** (`test/test_hardware_interface.cpp`):
   ```cpp
   // Verifies the plugin can be loaded and on_init succeeds with valid URDF parameters
   // Uses hardware_interface::ResourceManager in a test fixture
   TEST(HardwareInterfaceTest, PluginLoadsSuccessfully) {
     // Load the plugin via pluginlib
     pluginlib::ClassLoader<hardware_interface::SystemInterface> loader(
       "hardware_interface", "hardware_interface::SystemInterface");
     auto hw = loader.createSharedInstance("mecanum_pico/MecanumPicoHardware");
     ASSERT_NE(hw, nullptr);
   }

   TEST(HardwareInterfaceTest, ExportsFourCommandInterfaces) {
     // Instantiate with mock HardwareInfo containing 4 joints
     // Verify command_interfaces.size() == 4
   }

   TEST(HardwareInterfaceTest, ExportsFourStateInterfaces) {
     // Verify state_interfaces.size() == 8 (position + velocity per wheel)
   }
   ```

### TDD Strategy
- `colcon build && colcon test` → all suites pass.
- **Dry-run launch** (no Pico connected) — verify the controller manager loads and lists interfaces:
  ```bash
  ros2 launch mecanum_pico mecanum_pico.launch.py use_mock_hardware:=true
  ros2 control list_hardware_interfaces
  # Expected output:
  # command interfaces:
  #   front_left_wheel_joint/velocity [available] [claimed]
  #   front_right_wheel_joint/velocity [available] [claimed]
  #   rear_left_wheel_joint/velocity [available] [claimed]
  #   rear_right_wheel_joint/velocity [available] [claimed]
  ```

### Documentation Requirements
- `README.md`: Add "Controller Configuration" section with the complete `controllers.yaml` annotated with `# MEASURE YOUR ROBOT` for physical parameters.
- Code comment on `sum_of_robot_center_projection_on_X_Y_axis`: Explain the formula `lx + ly` where `lx` is half the wheelbase and `ly` is half the track width.

---

## Sprint 4 — Pico Firmware: Extend to 4-Motor Command Parsing

### Objective
Minimal changes to the Pico-side firmware to parse the 4-value command frame and drive 4 independent motor channels.

### Sub-Tasks

> The Pico firmware is typically written in C using the Pico SDK (or MicroPython). The existing 2-motor firmware likely has a `motorA`/`motorB` structure. We extend it to `motor[4]`.

1. **Audit existing firmware** — identify:
   - How it receives serial bytes (polling `getchar_timeout_us`, interrupt-driven, or DMA).
   - How it parses the `m <l> <r>\n` command.
   - How it drives motors (PWM via `pwm_set_wrap`/`pwm_set_chan_level`, or H-bridge direction + PWM).
   - How it reads encoders (interrupt-driven tick counters in `gpio_irq_callback`).
   - How it responds to the `e\n` request.

2. **Extend the motor struct** in firmware:
   ```c
   // pico_firmware/motor.h
   typedef struct {
     uint pwm_pin;
     uint dir_pin_a;
     uint dir_pin_b;
     volatile int32_t enc_count;  // incremented by GPIO IRQ
     uint enc_pin_a;
     uint enc_pin_b;
   } Motor;

   // In main.c:
   Motor motors[4];  // [0]=FL, [1]=FR, [2]=RL, [3]=RR
   ```

3. **Extend command parser**:
   ```c
   // Parse "m <fl> <fr> <rl> <rr>\n"
   void handle_command(const char * buf) {
     int32_t v[4];
     if (sscanf(buf, "m %d %d %d %d", &v[0], &v[1], &v[2], &v[3]) == 4) {
       for (int i = 0; i < 4; i++) {
         set_motor_speed(&motors[i], v[i]);
       }
     } else if (buf[0] == 'e') {
       // Respond with encoder counts
       printf("e %d %d %d %d\n",
         motors[0].enc_count, motors[1].enc_count,
         motors[2].enc_count, motors[3].enc_count);
     } else if (buf[0] == 'r') {
       for (int i = 0; i < 4; i++) motors[i].enc_count = 0;
       printf("OK\n");
     }
   }
   ```

4. **Extend the encoder IRQ handler** to handle 4 encoder pairs:
   ```c
   void gpio_irq_handler(uint gpio, uint32_t events) {
     for (int i = 0; i < 4; i++) {
       if (gpio == motors[i].enc_pin_a) {
         bool dir = gpio_get(motors[i].enc_pin_b);
         motors[i].enc_count += dir ? 1 : -1;
       }
     }
   }
   // Register all 8 encoder pins in main():
   for (int i = 0; i < 4; i++) {
     gpio_set_irq_enabled_with_callback(
       motors[i].enc_pin_a, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, &gpio_irq_handler);
   }
   ```

5. **Assign GPIO pins** — create a `board_config.h`:
   ```c
   // board_config.h  — ADJUST TO YOUR WIRING
   // Motor 0: Front Left
   #define FL_PWM_PIN   2
   #define FL_DIR_A_PIN 3
   #define FL_DIR_B_PIN 4
   #define FL_ENC_A_PIN 5
   #define FL_ENC_B_PIN 6
   // Motor 1: Front Right
   #define FR_PWM_PIN   7
   // ... (continue for RL, RR)
   ```

6. **Pico-side PID loop fix (Resolving the Bug):**
   The existing `do_pid()` function mathematically integrates its output due to `output += p->output`, which is a known bug inherited from old porting projects. We need to implement a standard Positional PID controller for the Mecanum wheels.
   
   **Code to change in `pico_firmware/lib/mecanum_interface/mecanum_controller.c`:**
   ```c
   static void do_pid(SetPointInfo* p)
   {
       // 1. Calculate Error
       int input = (int)(p->encoder - p->prev_enc);
       long perror = (long)(p->target) - input;
   
       // 2. Standard Positional PID Equation: Output = Kp * error + Ki * sum(error) - Kd * d(input)
       long output = (Kp * perror + p->iterm - Kd * (input - p->prev_input)) / Ko;
       
       // 3. Save states for next loop
       p->prev_enc = p->encoder;
       p->prev_input = input;
   
       // 4. Clamp output (Anti-windup logic)
       if (output >= MAX_PWM) {
           output = MAX_PWM;
       } else if (output <= -MAX_PWM) {
           output = -MAX_PWM;
       } else {
           // Only accumulate ITerm when not saturated
           p->iterm += Ki * perror;
       }
   
       // 5. Directly assign output (DO NOT USE += p->output)
       p->output = output; 
   }
   ```
   **Web Research Examples for Mecanum PID control in ROS 2 Humble:**
   Review these GitHub repositories for modern examples of correctly implemented Arduino PID firmware interfacing natively with ROS 2 Humble:
   1. [roboTHIx / mecanum_controller](https://github.com/roboTHIx/mecanum_controller): A complete `ros2_control` hardware interface and controller module optimized specifically for 4-wheel mecanum robots and tested extensively natively with ROS 2 Humble. 
   2. [deborggraever / ros2-mecanum-bot](https://github.com/deborggraever/ros2-mecanum-bot): A full ROS 2 Mecanum wheel robot example tested specifically on Ubuntu 22.04 LTS and ROS 2 Humble LTS using standard kinematics arrays.
   3. [Tarekshohdy688 / Mobile_Macnum_Robot](https://github.com/Tarekshohdy688/Mobile_Macnum_Robot): Designed for a 4WD Mecanum Mobile Robot supporting both ROS 1 and ROS 2 Humble. It includes `Motors_code.ino` for an Arduino Mega 2560 showing the distinct separation of the motor firmware from the Humble controller PC.
   4.    **Web Research Examples for Mecanum PID control in Arduino:**
   Review these GitHub repositories for canonical examples of correctly implemented Arduino Mecanum PID velocity drives:
   1. [qooiprww / mecanum-wheel-Robot-PID-control](https://github.com/qooiprww/mecanum-wheel-Robot-PID-control): A complete Arduino + L293D implementation employing the official `PID_v1` library for pure positional PID, avoiding the accumulation bug.
   2. [enVId-tech / Mecanum-Drive-Arduino](https://github.com/enVId-tech/Mecanum-Drive-Arduino): Shows a clear Arduino PID loop array structure tailored specifically for Mecanum wheels.
   3. [MoebiusTech / MecanumRobot-ArduinoMega2560](https://github.com/MoebiusTech/MecanumRobot-ArduinoMega2560): Professional Arduino Mega logic handling 4 controllers for mecanum kinematics correctly.

### TDD Strategy
- **Unit test on host** (using Pico SDK's host simulation or just compile with `-DPICO_SDK_SIMULATION`):
  Test `handle_command` with known inputs and assert `printf` output using a captured stdout.
- **HIL test 1 — loopback**: Connect Pico to host, send `m 50 50 50 50\n`, read `e\n` response, assert 4 values are incrementing.
- **HIL test 2 — motor response**: Command each motor independently with positive/negative values; verify direction and speed using a tachometer or oscilloscope on encoder pins.

### Documentation Requirements
- `pico_firmware/README.md`: Document all GPIO pin assignments and the physical motor-to-array-index mapping with a diagram.
- `board_config.h`: Inline comment on every `#define` with the physical connector label.

---

## Sprint 5 — Protocol Refinement: Float Velocity Commands (Optional Upgrade)

### Objective
Optionally migrate from ticks-per-loop integers to floating-point `rad/s` directly on the wire. This simplifies the host-side `write()` and moves unit conversion entirely to the Pico, improving composability.

### Sub-Tasks

1. **Update wire protocol**:

   | Direction | New format | Example |
   |-----------|-----------|---------|
   | Host → Pico | `m <fl_rps> <fr_rps> <rl_rps> <rr_rps>\n` | `m 1.57 -1.57 1.57 -1.57\n` |

2. **Update `pico_comms.hpp`**:
   ```cpp
   void setMotorValues(double fl, double fr, double rl, double rr) {
     std::stringstream ss;
     ss << std::fixed << std::setprecision(3)
        << "m " << fl << " " << fr << " " << rl << " " << rr << "\n";
     sendRaw(ss.str());
   }
   ```

3. **Update `write()` in `mecanum_pico.cpp`** — send `cmd` directly (already in `rad/s`):
   ```cpp
   comms_.setMotorValues(wheel_fl_.cmd, wheel_fr_.cmd, wheel_rl_.cmd, wheel_rr_.cmd);
   ```

4. **Update Pico parser** to use `sscanf` with `%f`:
   ```c
   float v[4];
   if (sscanf(buf, "m %f %f %f %f", &v[0], &v[1], &v[2], &v[3]) == 4) {
     // Convert rad/s to PWM via: pwm = v[i] * (max_pwm / max_rad_per_s)
   }
   ```

### TDD Strategy
- Regression: re-run all Sprint 2 unit tests with updated mock format.
- HIL: Verify the Pico receives float commands correctly with `minicom` before activating from ROS.

### Documentation Requirements
- Update the "Serial Protocol" section in `README.md` to reflect the float format.
- Note that this is a **breaking change** in the protocol version — consider adding a `version\n` handshake command.

---

## Sprint 6 — Simulation Support: Gazebo `mock_hardware`

### Objective
Ensure the package works in simulation without a Pico attached, using ROS 2 Control's `mock_components/GenericSystem` — critical for CI and algorithm development.

### Sub-Tasks

1. **Create a `fake` hardware descriptor** (`fake_mecanum_hardware.xml` / xacro macro):
   ```xml
   <!-- ros2_control.xacro — simulation block -->
   <xacro:if value="$(arg use_mock_hardware)">
     <ros2_control name="MecanumMockHardware" type="system">
       <hardware>
         <plugin>mock_components/GenericSystem</plugin>
       </hardware>
       <joint name="front_left_wheel_joint">
         <command_interface name="velocity"/>
         <state_interface name="velocity"><param name="initial_value">0.0</param></state_interface>
         <state_interface name="position"><param name="initial_value">0.0</param></state_interface>
       </joint>
       <!-- Repeat for other 3 joints -->
     </ros2_control>
   </xacro:if>
   ```

2. **Update launch file** to accept `use_mock_hardware` arg:
   ```python
   # mecanum_pico.launch.py
   use_mock_hardware = LaunchConfiguration('use_mock_hardware', default='false')
   ```

3. **Verify with Gazebo Ignition** (Fortress): The `ign_ros2_control` plugin should expose the same 4 joints if running a full sim.

4. **Add a CI launch test** in `test/`:
   ```python
   # test/test_launch.py (using launch_testing)
   @launch_testing.decorators.keep_alive
   def generate_test_description():
       return launch.LaunchDescription([
           IncludeLaunchDescription(
               PythonLaunchDescriptionSource([...mecanum_pico.launch.py']),
               launch_arguments={'use_mock_hardware': 'true'}.items()
           ),
           launch_testing.actions.ReadyToTest()
       ])

   class TestControllerManager(unittest.TestCase):
       def test_interfaces_listed(self, launch_service, proc_output):
           # ros2 control list_hardware_interfaces → assert 4 velocity commands exist
   ```

### TDD Strategy
- `colcon test` → launch test passes in < 30 s.
- Manually drive with `teleop_twist_keyboard` in mock mode — all 4 velocity state interfaces update in `ros2 control list_hardware_interfaces`.

### Documentation Requirements
- `README.md`: Add a "Simulation" section with the exact launch command and expected terminal output.

---

## Sprint 7 — Physical Calibration & HIL Validation

### Objective
Drive a physical robot, validate kinematics parameters, and produce a calibration guide.

### Sub-Tasks

1. **Encoder calibration**:
   - Command `m 0 0 0 0\n` (stop).
   - Manually rotate each wheel exactly one full revolution.
   - Read `e\n` response and record tick count → update `enc_counts_per_rev`.

2. **Wheel radius calibration**:
   - Drive straight at `linear.x = 0.1 m/s` for 1 m (timed or measured).
   - Compare `/odom` displacement to ground truth.
   - Adjust `wheels_radius` in `controllers.yaml`.

3. **`sum_of_robot_center_projection_on_X_Y_axis` calibration**:
   - Command pure rotation (`angular.z = 1.0 rad/s`).
   - After one full revolution (6.28 s), check that `/odom` reports `~6.28 rad` rotation and `~0 m` translation.
   - If translation drift exists, adjust `lx + ly`.

4. **Strafing test** (mecanum-specific):
   - Command `linear.y = 0.1 m/s` (pure strafe).
   - Verify the robot moves laterally without rotation.
   - This is the critical mecanum sanity check — if FL/RR and FR/RL are swapped in the URDF or firmware, this will fail visibly.

5. **HIL test script** (`test/hil/test_mecanum_motion.py`):
   ```python
   # Publishes TwistStamped, records /odom for 2 s, asserts pose delta
   def test_strafe_left():
       pub.publish(TwistStamped(twist=Twist(linear=Vector3(y=0.1))))
       time.sleep(2.0)
       odom = last_odom
       assert abs(odom.pose.pose.position.y) > 0.15, "Robot did not strafe"
       assert abs(odom.pose.pose.position.x) < 0.05, "Robot drifted forward"
   ```

### TDD Strategy
- All HIL tests run via `pytest test/hil/` with a live robot connected.
- Gate the final merge on: straight drive ±5% error, rotation ±5%, strafe ±10%.

### Documentation Requirements
- `README.md`: Add a "Calibration" section with all 3 calibration procedures as numbered steps.
- Record your robot's measured values in `config/robot_params.yaml` with comments.

---

## File Changelist Summary

```
mecanum_pico/
├── CMakeLists.txt                       ← updated deps, plugin export, test targets
├── package.xml                          ← renamed, mecanum_drive_controller dep
├── mecanum_pico.xml                     ← plugin descriptor (was diffdrive_arduino.xml)
├── include/mecanum_pico/
│   ├── mecanum_pico.hpp                 ← 4 Wheel members, updated Config struct
│   ├── pico_comms.hpp                   ← 4-value setMotorValues / readEncoderValues
│   └── wheel.hpp                        ← unchanged (already wheel-agnostic)
├── src/
│   └── mecanum_pico.cpp                 ← on_init, export_*, read, write all updated
├── config/
│   └── my_controllers.yaml              ← mecanum_drive_controller + 4 joint names
├── launch/
│   └── mecanum_pico.launch.py           ← use_mock_hardware arg added
├── description/
│   └── ros2_control.xacro              ← 4 joints declared
├── test/
│   ├── test_wheel.cpp                   ← Sprint 1 unit tests
│   ├── test_pico_comms.cpp              ← Sprint 2 unit tests
│   ├── test_hardware_interface.cpp      ← Sprint 3 plugin load tests
│   ├── test_launch.py                   ← Sprint 6 CI launch tests
│   └── hil/
│       └── test_mecanum_motion.py       ← Sprint 7 HIL motion tests
└── pico_firmware/
    ├── CMakeLists.txt
    ├── board_config.h                   ← GPIO pin assignments
    ├── motor.h                          ← Motor struct (4-element array)
    ├── main.c                           ← command parser, PID loop
    └── README.md                        ← wiring diagram, pin table
```

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Wheel index/direction mismatch (FL↔RR swap) | Robot spins instead of strafing | Sprint 7 strafe test catches this immediately; label wheels in firmware with physical direction arrows |
| `sum_of_robot_center_projection_on_X_Y_axis` wrong | Odometry drift in rotation | Rotation calibration in Sprint 7; start with measured chassis dimensions |
| Serial buffer overflow at 30 Hz | Encoder data loss | Profile with `top` and `htop` on the host; reduce rate to 20 Hz if needed; use non-blocking reads with a circular buffer on Pico |
| `mecanum_drive_controller` not in Humble apt | Build fails | Build from source: `sudo apt install ros-humble-mecanum-drive-controller` — verify package exists; fall back to `ros-humble-ros2-controllers` source build |
| Pico USB-CDC re-enumeration on reset | Serial port changes to `/dev/ttyACM1` | Use udev rule: `SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", SYMLINK+="pico_mecanum"` |

---

## Definition of Done (per Sprint)

- [ ] All unit tests pass (`colcon test`)
- [ ] No compiler warnings at `-Wall -Wextra`
- [ ] Code reviewed and matches the style of the original `diffdrive_arduino`
- [ ] `README.md` updated with sprint deliverables
- [ ] Git tag created: `v0.X.0-sprintN-complete`
