# Robot


## 
This repository contains code and configurations for a robot project using ROS 2 Humble and Gazebo simulation.

## Installation
To set up the necessary ROS 2 packages, run the following command:


### Companion PC
```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gazebo-ros2-control 
sudo apt install python3-colcon-common-extensions
sudo apt install ros-humble-xacro ros-humble-joint-state-publisher-gui
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-twist-mux
sudo apt install ros-humble-xacro ros-humble-joint-state-publisher-gui
```
colcon build --symlink-install
```yaml
network:
  version: 2
  renderer: NetworkManager
  
  ethernets:
    eth0:
      dhcp4: no
#      addresses: [192.168.178.50/24]
      gateway4: 192.168.178.1
      nameservers:
        addresses: [192.168.178.1]
```

### Raspberry Pi
```bash
sudo apt-get install netplan.io python3-colcon-common-extensions libraspberrypi-bin v4l-utils ros-humble-v4l2-camera ros-humble-image-transport-plugins
sudo apt install libraspberrypi-bin v4l-utils ros-humble-v4l2-camera ros-humble-image-transport-plugins
```
Tailscale Installation:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Dienst aktivieren und starten:
```bash
sudo systemctl enable --now tailscaled
```
Tailscale anmelden:
```bash
sudo tailscale up
```
tailscale ssh nutzen um sich vom Companion PC auf den Raspberry Pi zu verbinden:
```bash
sudo tailscale set --ssh
```

Nützliche Prüfbefehle:
```bash
tailscale status
tailscale ip
ip addr show tailscale0
sudo systemctl status tailscaled --no-pager
```

Backup vorhandener Netplan-Dateien:
```bash
sudo mkdir -p /etc/netplan/backup
sudo cp /etc/netplan/*.yaml /etc/netplan/backup/backup-$(date +%F_%H%M%S).yaml
```
danach die neue Netplan-Konfiguration erstellen mit `nano /etc/netplan/50-wifi.yaml` und folgendem Inhalt: 

```yaml
# Network configuration for Raspberry Pi
network:
  version: 2
  renderer: NetworkManager

  wifis:
    wlan0:
      dhcp4: no
      addresses: [192.168.178.45/24]
      gateway4: 192.168.178.1
      nameservers:
        addresses: [192.168.178.1]
      access-points:
        "MochauMilkhome5G":
          password: "//PS4kko!!//"
```
Generieren und anwenden:

```bash
sudo netplan generate
sudo netplan apply
```
Kurz prüfen (IP, Gateway, Tailscale):


```bash
sudo usermod -aG video $USER
vcgencmd get_camera
v4l2-ctl --list-devices
```



## CycloneDDS Configuration (VPN Setup)

We use a **Strict VPN** configuration using Tailscale to ensure reliable connectivity between PC and Pi, avoiding local network routing conflicts.

### Quick Setup (Persistence)
Add these lines to your `~/.bashrc` on both the PC and Raspberry Pi:

```bash
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

### Troubleshooting
If connections fail:
1. Ensure Tailscale is up: `tailscale status`
2. Check env vars: `echo $CYCLONEDDS_URI`
3. Restart ROS 2 daemon: `ros2 daemon stop`



## Bash änderungen

```bash
alias ws='source install/setup.bash'


source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```
Umgebungsvariablen prüfen:

printenv | grep -E "ROS|DDS|RMW"
ROS_VERSION=2
ROS_PYTHON_VERSION=3
ROS_DOMAIN_ID=0
ROS_LOCALHOST_ONLY=0
CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
ROS_DISTRO=humble
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


Simulation starten
ros2 launch gubot_one launch_sim.launch.py world:=/home/ros/projects/my_new_robot/worlds/obstacles.world