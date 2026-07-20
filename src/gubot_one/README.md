# gubot_one

ROS 2 Humble + Gazebo (Ignition Fortress) Roboter-Projekt: 4-Rad-Mecanum-
Antrieb, IMU, Kamera, optionaler Nerf-Dart-Launcher. Läuft simuliert
(WSL2/PC) und auf echter Hardware (Raspberry Pi + Companion-PC über
Tailscale).

`gubot_one` ist ein **Metapaket** (nach dem Muster von `rosbot_ros`), das
nur die Abhängigkeiten der sechs Einzelpakete bündelt. Jedes Paket hat sein
eigenes README mit Startbefehlen, Launch-Argumenten und Beispielen:

| Paket | Inhalt | README |
|-------|--------|--------|
| `gubot_description`  | URDF/Xacro, Meshes, RViz-Configs, `load_urdf.launch.py` | [→](../gubot_description/README.md) |
| `gubot_controller`   | ros2_control-Bringup: `controller.launch.py`, `controllers.yaml`, `twist_mux.yaml` | [→](../gubot_controller/README.md) |
| `gubot_gazebo`       | Simulation: `simulation.launch.py`, Welten, Bridge-Configs — **Haupt-Einstieg für die Sim** | [→](../gubot_gazebo/README.md) |
| `gubot_localization` | EKF (`robot_localization`): `ekf.launch.py`, `ekf.yaml` | [→](../gubot_localization/README.md) |
| `gubot_bringup`      | Echter Roboter: `launch_all_real.launch.py`, Joystick, Kamera, LiDAR — **Haupt-Einstieg für Hardware** | [→](../gubot_bringup/README.md) |
| `gubot_utils`        | Teleop-Skripte, Autostart-Service, CycloneDDS-Configs, Setup-Skripte | [→](../gubot_utils/README.md) |

## Installation (Workspace)

```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gazebo-ros2-control
sudo apt install python3-colcon-common-extensions
sudo apt install ros-humble-xacro ros-humble-joint-state-publisher-gui
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-twist-mux
sudo apt install libserial-dev v4l-utils ros-humble-v4l2-camera ros-humble-image-transport-plugins

cd ~/projects/my_new_robot_9e34131   # Workspace-Root
colcon build --symlink-install
source install/setup.bash
```

## Simulation starten

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 launch gubot_gazebo simulation.launch.py
```

Details/Optionen (Welt wechseln, Kamera abschalten, Startpose, …) siehe
[`gubot_gazebo/README.md`](../gubot_gazebo/README.md).

```bash
# Karteileichen nach abgebrochenem Lauf beseitigen:
pkill -9 -f "ign gazebo" ; pkill -9 rviz2
ps aux | grep -E "(ign gazebo|launch)" | grep -v grep
ros2 daemon stop
```

## Echten Roboter starten (Raspberry Pi)

```bash
cd ~/projects/my_new_robot_9e34131
colcon build --symlink-install
source install/setup.bash

ros2 launch gubot_bringup launch_all_real.launch.py
# oder komfortabler mit Kurz-Flags:
./src/gubot_utils/scripts/start_robot.sh --face
```

Details/Optionen (LiDAR, Kamera, Gesichtsverfolgung, Autostart als
systemd-Service) siehe [`gubot_bringup/README.md`](../gubot_bringup/README.md)
und [`gubot_utils/README.md`](../gubot_utils/README.md).

### Firmware (Pi Pico)

Pin-Belegung und Flash-Anleitung: `src/diffdrive_arduino/firmware/README.md`.
Kurzfassung: Arduino IDE + `arduino-pico`-Core installieren,
`ROSArduinoBridge.ino` öffnen, Board „Raspberry Pi Pico“ wählen, hochladen.

## Netzwerk: PC ↔ Pi über Tailscale

Companion-PC und Raspberry Pi kommunizieren ausschließlich über ein
Tailscale-VPN (vermeidet Routing-Konflikte im lokalen WLAN). CycloneDDS-
Konfiguration, Setup-Skripte und Env-Variablen:
[`gubot_utils/README.md`](../gubot_utils/README.md#cyclonedds-über-tailscale-pc--pi).

<details>
<summary>Ersteinrichtung Tailscale + Netzwerk (einmalig, pro Rechner)</summary>

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled
sudo tailscale up
sudo tailscale set --ssh   # SSH über Tailscale vom Companion-PC zum Pi
```

Prüfen:

```bash
tailscale status
tailscale ip
ip addr show tailscale0
sudo systemctl status tailscaled --no-pager
```

**Companion-PC** — statisches Ethernet, Beispiel `/etc/netplan/*.yaml`:

```yaml
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      dhcp4: no
      gateway4: 192.168.178.1
      nameservers:
        addresses: [192.168.178.1]
```

**Raspberry Pi** — WLAN, Beispiel `/etc/netplan/50-wifi.yaml`:

```yaml
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
        "<SSID>":
          password: "<passwort>"
```

```bash
sudo mkdir -p /etc/netplan/backup
sudo cp /etc/netplan/*.yaml /etc/netplan/backup/backup-$(date +%F_%H%M%S).yaml
sudo netplan generate
sudo netplan apply
```

Raspberry-Pi-Kamera:

```bash
sudo apt-get install netplan.io python3-colcon-common-extensions libraspberrypi-bin v4l-utils ros-humble-v4l2-camera ros-humble-image-transport-plugins
sudo usermod -aG video $USER
vcgencmd get_camera
v4l2-ctl --list-devices
```

</details>

## Externe Pakete (`serial`, `diffdrive_arduino`)

```bash
cd src/
git clone https://github.com/joshnewans/serial
git clone https://github.com/joshnewans/diffdrive_arduino
cd diffdrive_arduino && git branch -a && git switch humble
```
