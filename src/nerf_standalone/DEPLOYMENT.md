# Deployment Instructions - Nerf Robot on Raspberry Pi

## 1. Sync Code to Raspberry Pi
SSH into the Raspberry Pi and pull the latest changes:
```bash
ssh ros@<RASPBERRY_IP>
cd ~/dev_bot
git pull
```

## 2. Build Firmware
### Nerf Controller (Arduino Nano / Micro)
1.  Connect the Nerf Arduino to your PC (or compile on Pi if setup).
2.  Open `src/nerf_standalone/firmware/nerf_micro/nerf_micro.ino`.
3.  Select Board and Port.
4.  Upload.

### Base Controller (Arduino Mega / Uno)
1.  Connect the Base Arduino.
2.  Open `src/diffdrive_arduino/firmware/ROSArduinoBridge/ROSArduinoBridge.ino`.
3.  Upload.

## 3. Build ROS Workspace
On the Raspberry Pi:
```bash
cd ~/dev_bot
colcon build --symlink-install
source install/setup.bash
```

## 4. Run Full System Test
Ensure both Arduinos are connected (`/dev/ttyACM0`, `/dev/ttyUSB0` etc - check permissions!).
```bash
python3 src/nerf_standalone/scripts/full_system_test.py
```

## 5. Standard Launch
To run the full robot stack:
```bash
ros2 launch gubot_one robot.launch.py
```
(Or whichever main launch file wraps both base and launcher)
