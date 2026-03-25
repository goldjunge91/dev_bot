# Plan 03 — IMU: `orientation` State-Interfaces fehlen

> [!IMPORTANT]
> **Workflow (copilot-instructions):** Test zuerst → Implementierung → alten Code auskommentieren (nicht löschen). C++: `gtest`. XACRO: `ament_xmllint`.

## Problem

`ros2_control_hardware.xacro`: IMU-Sensor hat kein `orientation.x/y/z/w` State-Interface.  
→ `nav2` / `robot_localization` erhalten kein vollständiges `sensor_msgs/Imu` → Navigation blockiert.

**Soll:**
```xml
<state_interface name="orientation.x"/>
<state_interface name="orientation.y"/>
<state_interface name="orientation.z"/>
<state_interface name="orientation.w"/>
```

---

## Tasks

### Task 1 — Tests schreiben (TDD: erst fehlschlagend)

#### 1a — XACRO-Test (pytest)
- [ ] **1.1** `src/gubot_one/test/test_ros2_control_hardware_xacro.py` anlegen
- [ ] **1.2** Test: XACRO rendern → URDF parsen → `imu_sensor` hat `orientation.x/y/z/w` als `state_interface`
- [ ] **1.3** Test ausführen → **muss rot sein**
  ```bash
  colcon test --packages-select gubot_one --pytest-args -k test_ros2_control_hardware_xacro
  ```

#### 1b — Plugin-Test (gtest, falls Plugin erweitert wird)
- [ ] **1.4** `src/mecanum_pico/test/test_mecanum_pico_hardware.cpp` anlegen  
  (via `ament_cmake_gtest`)
- [ ] **1.5** Test: `export_state_interfaces()` liefert Interface mit Name `imu_sensor/orientation.x`
- [ ] **1.6** Test ausführen → **muss rot sein**
  ```bash
  colcon test --packages-select mecanum_pico
  ```

### Task 2 — Analyse (KISS: minimale Änderung)
- [ ] **2.1** `MecanumPicoHardware.cpp`: `export_state_interfaces()` lesen — liefert es bereits `orientation.*`?
- [ ] **2.2** Wenn ja: nur xacro anpassen (kein Plugin-Eingriff nötig)
- [ ] **2.3** Wenn nein: Plugin-Erweiterung erforderlich (Tasks 4)

### Task 3 — XACRO aktualisieren
- [ ] **3.1** `ros2_control_hardware.xacro`: 4 `<state_interface name="orientation.*"/>` einfügen  
  (Kommentar: `<!-- Required by imu_sensor_broadcaster and robot_localization -->`)
- [ ] **3.2** `ament_xmllint` ausführen

### Task 4 — Plugin erweitern (nur falls Task 2.3 zutrifft)
- [ ] **4.1** `MecanumPicoHardware.hpp`: Member `double imu_orientation_[4] = {0.0, 0.0, 0.0, 1.0};` hinzufügen  
  (Identity-Quaternion als sicherer Default)
- [ ] **4.2** `MecanumPicoHardware.cpp` — `export_state_interfaces()`: alten Block auskommentieren, neuen darunter:
  ```cpp
  // OLD (auskommentiert):
  // hardware_interface::StateInterface(info_.sensors[0].name, "angular_velocity.z", ...)
  // NEW:
  hardware_interface::StateInterface(info_.sensors[0].name, "orientation.x", &imu_orientation_[0]),
  // ... .y, .z, .w analog
  ```
- [ ] **4.3** In `read()`: `RCLCPP_INFO` Log wenn Orientation-Daten empfangen werden:
  ```cpp
  RCLCPP_INFO(rclcpp::get_logger("MecanumPicoHardware"),
    "{\"event\": \"imu_orientation\", \"w\": %f}", imu_orientation_[3]);
  ```
- [ ] **4.4** Naming: Variablen `snake_case` (`imu_orientation_`), keine temporären Helfer unnötig
- [ ] **4.5** `colcon build --packages-select mecanum_pico`

### Task 5 — Linter & Tests grün
- [ ] **5.1** `ament_cpplint src/mecanum_pico/src/MecanumPicoHardware.cpp`
- [ ] **5.2** `ament_cppcheck src/mecanum_pico/src/`
- [ ] **5.3** Alle Tests erneut ausführen → **müssen grün sein**

### Task 6 — Manuelle Verifikation
- [ ] **6.1** `ros2 control list_hardware_interfaces` → `imu_sensor/orientation.x [available]`
- [ ] **6.2** `ros2 topic echo /imu_sensor/imu` → `orientation.w` ≥ 0.99 (Identity)
- [ ] **6.3** EKF-Node starten → kein Warning über fehlende Orientation

---

## Betroffene Dateien

- **[NEW]** `src/gubot_one/test/test_ros2_control_hardware_xacro.py`
- **[NEW]** `src/mecanum_pico/test/test_mecanum_pico_hardware.cpp` *(falls Plugin-Erweiterung)*
- **[MODIFY]** `src/gubot_one/description/urdf/ros2_control_hardware.xacro`
- **[MODIFY]** `src/mecanum_pico/src/MecanumPicoHardware.cpp` *(falls Plugin-Erweiterung)*
- **[MODIFY]** `src/mecanum_pico/include/mecanum_pico/MecanumPicoHardware.hpp` *(falls Plugin-Erweiterung)*

---

## Verifikationskriterium

> Alle gtest- und pytest-Tests grün. `ros2 topic echo /imu_sensor/imu` zeigt `orientation.w ≈ 1.0`. EKF ohne Warnings.
