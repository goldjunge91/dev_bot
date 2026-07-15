# gubot_localization

`robot_localization`-EKF (`ekf_node`), fusioniert Rad-Odometrie
(`odometry/wheels`, nur vx/vy/vyaw) und IMU (`imu/data`, nur Yaw +
Winkelgeschwindigkeiten) zu `odom → base_link` TF + `/odometry/filtered`.
Läuft im 2D-Modus (`two_d_mode: true`).

Wird eingebunden von `gubot_gazebo/launch/spawn_robot.launch.py` (Sim) und
`gubot_bringup/launch/launch_all_real.launch.py` (echte Hardware) — nötig,
weil der `mecanum_drive_controller` selbst **kein** TF publiziert
(`enable_odom_tf: false` in `gubot_controller/config/controllers.yaml`).

## Inhalt

```
launch/ekf.launch.py   # startet robot_localization/ekf_node
config/ekf.yaml        # Sensor-Fusion-Konfiguration
```

## Schnellstart

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to gubot_localization
source install/setup.bash

ros2 launch gubot_localization ekf.launch.py
```

> Kein eigenständig sinnvoller Start — braucht laufende `odometry/wheels`-
> und `imu/data`-Topics (also `gubot_controller` bzw. die Sim/Hardware).
> `use_sim_time` wird **nicht** hier gesetzt, sondern global via
> `SetParameter` in `gubot_gazebo/launch/simulation.launch.py`
> propagiert — auf echter Hardware bleibt es auf `false` (Default).

## Launch-Argumente

Keine — `ekf.launch.py` hat keine `DeclareLaunchArgument`s. Alle Tuning-
Parameter stecken in `config/ekf.yaml`, dort ansetzen und neu launchen.

## Wichtigste Parameter (`config/ekf.yaml`)

| Parameter | Wert | Bedeutung |
|---|---|---|
| `frequency` | 20.0 Hz | EKF-Update-Rate. |
| `two_d_mode` | `true` | Ignoriert z/roll/pitch. |
| `odom0` | `odometry/wheels` | Quelle: `mecanum_drive_controller`-Odometrie, nur `vx/vy` + `vyaw` einbezogen (`odom0_config`). |
| `imu0` | `imu/data` | Quelle: `imu_broadcaster`, nur Yaw + `vyaw` einbezogen, `imu0_remove_gravitational_acceleration: true`. |
| `publish_tf` | `true` | Publiziert `odom → base_link`. |
| `dynamic_process_noise_covariance` | `true` | Passt Prozessrauschen dynamisch an (experimentell eingemessen). |

## Nützliche Introspektions-Befehle

```bash
ros2 topic echo /odometry/filtered
ros2 run tf2_ros tf2_echo odom base_link
ros2 run rqt_tf_tree rqt_tf_tree     # TF-Baum prüfen (odom -> base_link -> ...)
```
