# Robot


## 
This repository contains code and configurations for a robot project using ROS 2 Humble and Gazebo simulation.

## Installation
To set up the necessary ROS 2 packages, run the following command:


### Companion PC
```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gazebo-ros2-control
sudo apt install python3-colcon-common-extensions
```

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
sudo apt-get install netplan.io python3-colcon-common-extensions
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
sudo apt install ros-humble-xacro ros-humble-joint-state-publisher-gui
```


