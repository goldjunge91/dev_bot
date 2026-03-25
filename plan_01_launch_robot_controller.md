# Plan 01 — `launch_robot.launch.py`: Falscher Controller

> [!IMPORTANT]
> **Workflow (copilot-instructions):** Test zuerst schreiben → Implementierung → alten Code auskommentieren (nicht löschen).

## Problem

`launch_robot.launch.py` startet `diff_cont` statt `mecanum_cont`.

| Ist | Soll |
|---|---|
| Controller: `diff_cont` | `mecanum_cont` |
| Config: `my_controllers.yaml` | `mecanum_my_controllers.yaml` |
| Remap: `/diff_cont/cmd_vel_unstamped` | `/mecanum_cont/reference_unstamped` |
| kein `drive_type` Argument | `drive_type` mit Default `mecanum` |

---

## Tasks

### Task 1 — Test schreiben (TDD: erst fehlschlagend)
- [ ] **1.1** pytest-Testdatei anlegen: `src/gubot_one/test/test_launch_robot.py`
- [ ] **1.2** Test: `launch_robot.launch.py` parsen → prüfen dass kein Node mit `diff_cont` vorhanden ist
- [ ] **1.3** Test: Argument `drive_type` existiert in der LaunchDescription
- [ ] **1.4** Test: Controller-Spawner enthält `mecanum_cont` als Controller-Name
- [ ] **1.5** Tests ausführen → **müssen rot sein** (sonst ist der Bug nicht reproduziert)
  ```bash
  cd /home/ros/projects/my_new_robot_9e34131
  colcon test --packages-select gubot_one --pytest-args -k test_launch_robot
  ```

### Task 2 — Analyse (KISS: minimale Änderung finden)
- [ ] **2.1** `launch_robot.launch.py` öffnen, alle `diff_cont`-Vorkommen zählen
- [ ] **2.2** `launch_sim.launch.py` als Referenz öffnen (zeigt korrekte mecanum-Konfiguration)
- [ ] **2.3** `mecanum_my_controllers.yaml` prüfen: `mecanum_cont` korrekt als Node-Name definiert?

### Task 3 — Implementierung
- [ ] **3.1** `drive_type` Launch-Argument hinzufügen (Default: `mecanum`):
  ```python
  # --- OLD (auskommentieren, nicht löschen) ---
  # DeclareLaunchArgument('use_sim_time', ...)
  # --- NEW ---
  DeclareLaunchArgument('drive_type', default_value='mecanum', ...),
  ```
- [ ] **3.2** Controller-Manager: `my_controllers.yaml` → `mecanum_my_controllers.yaml` (alten Pfad auskommentieren)
- [ ] **3.3** Spawner: `diff_cont` → `mecanum_cont` (alte Zeile auskommentieren)
- [ ] **3.4** twist_mux Remap: `/diff_cont/cmd_vel_unstamped` → `/mecanum_cont/reference_unstamped` (alte Zeile auskommentieren)
- [ ] **3.5** `drive_type` an RSP weiterleiten

### Task 4 — Linter & Tests grün
- [ ] **4.1** Linter lokal ausführen:
  ```bash
  ament_flake8 src/gubot_one/launch/launch_robot.launch.py
  ament_pep257 src/gubot_one/launch/launch_robot.launch.py
  ```
- [ ] **4.2** Tests erneut ausführen → **müssen jetzt grün sein**
- [ ] **4.3** Regressionstest: `launch_sim.launch.py` weiterhin unverändert funktionsfähig

### Task 5 — Manuelle Verifikation
- [ ] **5.1** `ros2 launch gubot_one launch_robot.launch.py --show-args` → `drive_type` sichtbar
- [ ] **5.2** Auf Hardware: `ros2 control list_controllers` → `mecanum_cont` ist `active`, `diff_cont` nicht vorhanden
- [ ] **5.3** `ros2 topic echo /mecanum_cont/reference_unstamped` → Topic existiert

---

## Betroffene Dateien

- **[NEW]** `src/gubot_one/test/test_launch_robot.py`
- **[MODIFY]** `src/gubot_one/launch/launch_robot.launch.py`

---

## Verifikationskriterium

> Alle pytest-Tests grün. `ros2 control list_controllers` zeigt `mecanum_cont [mecanum_drive_controller] active`. Kein `diff_cont` mehr aktiv.
