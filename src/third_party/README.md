# third_party

Fremdpakete, die nicht von uns gepflegt werden. Von pre-commit ausgenommen
(siehe `exclude` in `.pre-commit-config.yaml`). Eigene Änderungen hier
minimal halten und im jeweiligen Paket dokumentieren.

| Paket | Herkunft | Hinweis |
|-------|----------|---------|
| `serial` | <https://github.com/wjwwood/serial> | Sehr alt (package.xml Format 1); Kandidat für Ersatz durch einen gepflegten ROS-2-Fork. |
| `husarion_gz_worlds` | <https://github.com/husarion/husarion_gz_worlds> | Gazebo-Welten/Modelle von Husarion, unverändert. |
| `mecanum_drive_controller` | Adaptiert aus `diff_drive_controller` (<https://github.com/ros-controls/ros2_controllers>) | Lokale Anpassung für Mecanum-Kinematik. |
