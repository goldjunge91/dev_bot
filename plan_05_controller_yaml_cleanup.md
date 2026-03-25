# Plan 05 — `mecanum_my_controllers.yaml`: Doppelte Parameter aufräumen

> [!IMPORTANT]
> **Workflow (copilot-instructions):** Schema zuerst recherchieren → Test schreiben → YAML bereinigen. Alte Werte auskommentieren (nicht löschen). Kein /tmp.

## Problem

`mecanum_my_controllers.yaml` enthält doppelte Definitionen:
1. Wheel-Namen: `front_left_wheel_command_joint_name` **und** `front_left_wheel_name` (identisch)
2. Kinematik: `wheels_radius` in `kinematics:` Block **und** flach auf Controller-Ebene

→ Unklar welche Variante `mecanum_drive_controller` wirklich liest.

---

## Tasks

### Task 1 — Schema recherchieren (Voraussetzung für Test + Fix)
- [ ] **1.1** `mecanum_drive_controller` Parameter-Schema ermitteln:
  ```bash
  # Im laufenden System:
  ros2 param list /mecanum_cont
  ros2 param describe /mecanum_cont wheels_radius
  ```
- [ ] **1.2** Alternativ: ROS2 control Doku lesen:  
  `https://control.ros.org/rolling/doc/ros2_controllers/mecanum_drive_controller/doc/userdoc.html`
- [ ] **1.3** Ergebnis notieren: welcher Wheel-Name-Parameter und welcher Kinematik-Pfad ist korrekt?

### Task 2 — Test schreiben (TDD: erst fehlschlagend)
- [ ] **2.1** `src/gubot_one/test/test_controller_yaml.py` anlegen
- [ ] **2.2** Test: YAML laden → prüfen dass für jedes Rad **genau ein** Wheel-Name-Parameter existiert  
  (kein `_command_joint_name` UND `_name` gleichzeitig)
- [ ] **2.3** Test: `wheels_radius` erscheint **nicht** doppelt (einmal in `kinematics:`, einmal flach)
- [ ] **2.4** Test: YAML ist valides Python-dict (schlägt bei Syntax-Fehlern fehl)
- [ ] **2.5** Tests ausführen → **müssen rot sein** (Duplikate vorhanden)
  ```bash
  colcon test --packages-select gubot_one --pytest-args -k test_controller_yaml
  ```

### Task 3 — YAML bereinigen (KISS: minimale Änderung)
- [ ] **3.1** Falsche Wheel-Name-Variante auskommentieren (die andere stehen lassen):
  ```yaml
  # --- OLD (auskommentiert — falsche Variante nach Schema-Recherche):
  # front_left_wheel_command_joint_name: front_left_wheel_joint
  # --- NEW (korrekte Variante):
  front_left_wheel_name: front_left_wheel_joint
  ```
  *(Für alle 4 Räder wiederholen)*
- [ ] **3.2** Kinematik-Duplikate: falsche Ebene auskommentieren:
  ```yaml
  # --- OLD (auskommentiert):
  # wheels_radius: 0.05   # war auf Controller-Toplevel
  kinematics:
    wheels_radius: 0.05   # korrekte Position
  ```
- [ ] **3.3** Kommentar: `# Schema: mecanum_drive_controller v<x.y> — verified via ros2 param describe`

### Task 4 — Kinematik-Werte nach Plan 02 abstimmen
- [ ] **4.1** `sum_of_robot_center_projection_on_X_Y_axis` = `wheel_offset_x + wheel_offset_y` neu berechnen  
  (alten Wert auskommentieren, neuen darunter)
- [ ] **4.2** `wheels_radius` mit URDF-Geometrie abgleichen

### Task 5 — Validierung & Tests grün
- [ ] **5.1** YAML-Syntax:
  ```bash
  python3 -c "import yaml; yaml.safe_load(open('src/gubot_one/config/mecanum_my_controllers.yaml'))"
  ```
  *(Ausgabe ins Terminal — kein File-Write nach /tmp)*
- [ ] **5.2** Tests erneut ausführen → **müssen grün sein**
- [ ] **5.3** `ros2 param list /mecanum_cont` im laufenden System → keine Duplikate

---

## Betroffene Dateien

- **[NEW]** `src/gubot_one/test/test_controller_yaml.py`
- **[MODIFY]** `src/gubot_one/config/mecanum_my_controllers.yaml`

---

## Abhängigkeit

> [!NOTE]
> **Plan 02 muss abgeschlossen sein** bevor Task 4 ausgeführt wird, da `sum_of_...` vom korrigierten `wheel_offset_x` abhängt.

## Verifikationskriterium

> pytest grün. `ros2 param list /mecanum_cont` zeigt jeden Parameter **genau einmal**. Controller bleibt `active`.
