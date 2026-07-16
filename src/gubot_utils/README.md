# gubot_utils

Werkzeuge rund um `gubot_one`: Teleop-Skripte (Joystick + Tastatur),
Autostart als systemd-Service, CycloneDDS-Konfigurationen (Tailscale-VPN),
Setup-/Kalibrierungs-Skripte und Doku.

## Inhalt

```
scripts/teleop__nerf_joystick.py         # Joystick-Steuerung Nerf-Launcher (ros2 run)
scripts/teleop_twist_nerf_keyboard.py    # Tastatur-Steuerung Roboter + Nerf (ros2 run)
scripts/debug_tilt.py                    # Debug-Tool: prüft Tilt-Controller-Zustand
scripts/imu_hw_test.py                   # IMU-Hardware-Test (Rate, Bias, Drift, Gravitation)
scripts/start_robot.sh                   # Ein-Befehl-Start auf dem Roboter (Pi)
scripts/setup_dds_config.sh              # Kopiert CycloneDDS-Config nach /var/tmp/cyclonedds.xml
scripts/apply_bashrc_settings.sh         # Trägt ROS2/DDS-Env dauerhaft in ~/.bashrc ein
scripts/install_camera_calib.sh          # Symlinkt Kamera-Kalibrierung nach ~/.ros/camera_info/
autostart/gubot.service                  # systemd-Unit-Template (Platzhalter {{...}})
autostart/install_service.sh             # Installiert gubot.service (sudo, ersetzt Platzhalter)
cycloneDDS/pc_cyclonedds.xml             # DDS-Config für den Companion-PC (Tailscale-Peers)
cycloneDDS/raspi_cyclonedds.xml          # DDS-Config für den Raspberry Pi
docs/kamerakalibrierung.md               # Anleitung: Kamera-Kalibrierung über Tailscale
```

`scripts/*.py` sind über `ros2 run` erreichbar (installiert nach
`lib/gubot_utils/`), alle anderen Dateien (`.sh`, `.xml`, `docs/`) landen
unter `share/gubot_utils/` und werden per Pfad ausgeführt/referenziert.

## Teleop-Skripte

```bash
source install/setup.bash

# Joystick -> Nerf-Launcher (braucht laufenden joy_node, siehe gubot_bringup)
ros2 run gubot_utils teleop__nerf_joystick.py

# Tastatur -> Roboter-Bewegung (WASD) + Nerf-Launcher
ros2 run gubot_utils teleop_twist_nerf_keyboard.py
```

Tastenbelegung `teleop_twist_nerf_keyboard.py`:

| Taste | Aktion |
|---|---|
| `W`/`S`/`A`/`D` | Vorwärts/Rückwärts/Links drehen/Rechts drehen |
| `1` / `2` | Disarm / Arm |
| `SPACE` | Feuern |
| `T` / `G` | Tilt hoch/runter (±0.52 rad) |
| `R`/`F` | Power ±5 % |
| `E`/`D` | Power ±1 % |

Button-Mapping `teleop__nerf_joystick.py` (Xbox-Controller): `LB`+`RB`
3 s halten = Arm/Disarm, `LB`/`RB` einzeln = Tilt, `RT` = Feuern, D-Pad =
Notfall-Disarm.

## IMU-Hardware-Test (`imu_hw_test.py`)

Prüft die live IMU-Daten (`/imu/data`), während der Roboter **still
steht** (nicht bewegen!). Läuft auf dem Pi oder dem PC (gleiche
DDS-Config). Checks: Rate (~100 Hz), `frame_id` (`imu_link`),
Quaternion-Norm, Gyro-Bias im Stand, Gravitation (|accel| ≈ 9.81),
Yaw-Drift (Komplementärfilter), Timestamps. Exit-Code 0 = alles OK.

```bash
# Voraussetzung: launch_all_real.launch.py läuft
ros2 run gubot_utils imu_hw_test.py                      # 10 s Messung
ros2 run gubot_utils imu_hw_test.py --duration 30        # längere Messung
ros2 run gubot_utils imu_hw_test.py --min-rate 80        # strengere Rate
```

| Check | FAIL wenn | typische Ursache |
|---|---|---|
| Rate | < 50 Hz | controller_manager überlastet / DDS-Problem |
| frame_id | ≠ `imu_link` | controllers.yaml verstellt |
| Gyro-Ruhe | Bias > 0.05 rad/s | Roboter bewegt / Gyro-Kalibrierung |
| Yaw-Drift | > 2 °/s | Komplementärfilter/Gyro-Bias (Interim-Filter driftet leicht — WARN ab 0.2 °/s ist normal) |
| Gravitation | nur WARN | Accel-Skalierung/Achsen prüfen |

## Debug-Tool

```bash
# Während simulation.launch.py / launch_all_real.launch.py läuft:
ros2 run gubot_utils debug_tilt.py 2>&1 | tee debug_tilt.log
```
Prüft `controller_manager`-Status, geladene Hardware-Interfaces und
`JointState`/Tilt-Feedback — nützlich, wenn der Nerf-Tilt-Controller nicht
reagiert.

## Ein-Befehl-Start auf dem Roboter (`start_robot.sh`)

```bash
cd ~/projects/my_new_robot_9e34131   # Workspace-Root
./src/gubot_utils/scripts/start_robot.sh [OPTIONEN]
```

Baut intern auf `ros2 launch gubot_bringup launch_all_real.launch.py` auf
und übersetzt folgende Kurz-Flags:

| Flag | Bewirkt |
|---|---|
| `--face` | `launch_face_tracker:=true` |
| `--armed` | `auto_arm:=true` (Nerf-System sofort scharf — **Vorsicht**) |
| `--mjpg` (Standard) | `camera_type:=usb_cam` |
| `--yuyv` | `camera_type:=v4l2` |
| `--target <name>` | `target_person:=<name>` |
| `--search` | `allow_search:=true` |

```bash
# Beispiel: mit Gesichtsverfolgung, scharf, Zielperson "max"
./src/gubot_utils/scripts/start_robot.sh --face --armed --target max --search
```

Setzt automatisch `CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml`, falls
nicht bereits gesetzt (siehe DDS-Setup unten).

## CycloneDDS über Tailscale (PC ↔ Pi)

Die beiden Rechner kommunizieren ausschließlich über ein Tailscale-VPN
(vermeidet Routing-Konflikte im lokalen WLAN). Peer-IPs stehen in
`cycloneDDS/{pc,raspi}_cyclonedds.xml`.

```bash
# Einmalig auf JEDEM Rechner (PC und Pi getrennt, jeweils passende Datei!):
sudo cp src/gubot_utils/cycloneDDS/pc_cyclonedds.xml /var/tmp/cyclonedds.xml      # auf dem PC
sudo cp src/gubot_utils/cycloneDDS/raspi_cyclonedds.xml /var/tmp/cyclonedds.xml   # auf dem Pi
# oder (liest den Pfad aus setup_dds_config.sh, dort ggf. HOME anpassen):
bash src/gubot_utils/scripts/setup_dds_config.sh

export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
```

Dauerhaft eintragen (schreibt die Env-Variablen + Alias `ws` in
`~/.bashrc`, erkennt PC vs. Pi automatisch am Hostnamen `ros2pi`):

```bash
bash src/gubot_utils/scripts/apply_bashrc_settings.sh
source ~/.bashrc
```

Prüfen:

```bash
printenv | grep -E "ROS|DDS|RMW"
tailscale status
tailscale ip
ros2 daemon stop   # Domain-/RMW-Wechsel erzwingt Neustart des ROS2-Daemons
```

## Autostart als systemd-Service (auf dem Pi)

```bash
sudo bash src/gubot_utils/autostart/install_service.sh
```

Installiert `gubot.service` nach `/etc/systemd/system/`, ersetzt die
Platzhalter `{{WORKSPACE_DIR}}`/`{{START_SCRIPT_PATH}}` durch den
tatsächlichen Workspace-Pfad und führt `ExecStart=start_robot.sh --face`
aus. Danach:

```bash
sudo systemctl status gubot.service --no-pager
sudo systemctl restart gubot.service
sudo systemctl stop gubot.service
journalctl -u gubot.service -f       # Live-Log
```

## Kamera-Kalibrierung

```bash
bash src/gubot_utils/scripts/install_camera_calib.sh
```

Verlinkt `gubot_utils/config/camera_info/real_cam.yaml` nach
`~/.ros/camera_info/real_cam.yaml`. **Die Kalibrierungsdatei muss vorher
existieren** — Anleitung zum Erzeugen (Schachbrett, `camera_calibration`
über Tailscale) in [`docs/kamerakalibrierung.md`](docs/kamerakalibrierung.md).
