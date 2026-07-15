# Deployment Instructions - Nerf Robot on Raspberry Pi

## 1. Sync Code to Raspberry Pi
SSH into the Raspberry Pi and pull the latest changes:
```bash
ssh ros@<RASPBERRY_IP>
cd ~/dev_bot
git pull
```
 ls /dev/ttyACM* /dev/ttyUSB*
## 2. Build Firmware
### Nerf Controller (Arduino Nano / Micro)
1.  Connect the Nerf Arduino to your PC (or compile on Pi if setup).
2.  Open `src/nerf_launch_system/firmware/nerf_micro/nerf_micro.ino`.
3.  Select Board and Port.
4.  Upload.

### Base Controller (Raspberry Pi Pico)
1.  Connect the Pi Pico (holding BOOTSEL if needed).
2.  The firmware lives in `src/mecanum_pico/pico_firmware/` (PlatformIO project).
3.  Build & upload:
    ```bash
    cd src/mecanum_pico/pico_firmware
    pio run -t upload
    ```

## 3. Build ROS Workspace
On the Raspberry Pi:
```bash
cd ~/dev_bot
colcon build --symlink-install
source install/setup.bash
```

## 4. Launch Robot Stack
**Terminal 1:**
Launch the FULL robot (Base + Nerf + EKF + Joystick-Teleop) using the unified launch file:
```bash
ros2 launch gubot_bringup launch_all_real.launch.py
```
*Notes:*
- *Nerf hardware is enabled by default (`use_nerf_hardware:=true` inside the launch file); serial ports are resolved via `/dev/serial/by-id/...` in the URDF (`gubot_description/urdf/ros2_control_hardware.xacro`), not by ACM number.*
- *For joystick control, run `joy_node` on the remote machine with the gamepad (same `ROS_DOMAIN_ID`, CycloneDDS config from `src/gubot_utils/cycloneDDS/`); only `teleop_node`/`nerf_joy` run on the robot.*

## 5. Run Full System Test
**Terminal 2:**
While the launch file is running, execute the test script:
```bash
source install/setup.bash
python3 src/nerf_launch_system/scripts/full_system_test.py
```
