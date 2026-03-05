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
1.  Connect the Pi Pico (holding BOOTSEL if needed, though Arduino IDE usually handles it).
2.  Open `src/diffdrive_arduino/firmware/ROSArduinoBridge/ROSArduinoBridge.ino`.
3.  Ensure you have the **Raspberry Pi Pico/RP2040** board support installed (e.g., Earle Philhower core).
4.  Select Board: **Raspberry Pi Pico**.
5.  Upload.

## 3. Build ROS Workspace
On the Raspberry Pi:
```bash
cd ~/dev_bot
colcon build --symlink-install
source install/setup.bash
```

## 4. Launch Robot Stack
**Terminal 1:**
Launch the FULL robot (Base + Nerf) using the unified launch file:
```bash
ros2 launch gubot_one launch_robot.launch.py
```
*Note details: This assumes Nerf is on `/dev/ttyACM0` and Pico Base is on `/dev/ttyACM1`.*

## 5. Run Full System Test
**Terminal 2:**
While the launch file is running, execute the test script:
```bash
source install/setup.bash
python3 src/nerf_launch_system/scripts/full_system_test.py
```
