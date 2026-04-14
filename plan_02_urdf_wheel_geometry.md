# Plan 02 — URDF: Asymmetrische Vorderrad-Positionen

> [!IMPORTANT]
> **Workflow (copilot-instructions):** Test zuerst → Implementierung → alten Code auskommentieren (nicht löschen).

## Problem

`gubot_one_geometry.xacro`: Vorderräder haben keinen X-Offset (`xyz="0 ${wheel_offset_y} 0"`).  
→ Vorderachse bei X=0, Hinterachse bei X=−0.226. Mecanum-Controller erwartet symmetrisches Layout.

**Soll:** Alle 4 Räder symmetrisch um `base_link`:
```
front_{left/right}: xyz="+wheel_offset_x  ±wheel_offset_y  0"
rear_{left/right}:  xyz="-wheel_offset_x  ±wheel_offset_y  0"
```

---

## Tasks

### Task 1 — Test schreiben (TDD: erst fehlschlagend)
- [x] **1.1** pytest-Testdatei anlegen: `src/gubot_one/test/test_urdf_geometry.py`
- [x] **1.2** Test: XACRO rendern (`xacro gubot_one.urdf.xacro`), URDF parsen
- [x] **1.3** Test: `front_left_wheel_joint` origin X == `+wheel_offset_x` (≠ 0)
- [x] **1.4** Test: `front_right_wheel_joint` origin X == `+wheel_offset_x` (≠ 0)
- [x] **1.5** Test: Symmetrie — front X == −rear X für beide Seiten
- [x] **1.6** Tests ausführen → **müssen rot sein**
  ```bash
  colcon test --packages-select gubot_one --pytest-args -k test_urdf_geometry
  ```

### Task 2 — Analyse (KISS: minimale Änderung)
- [x] **2.1** `gubot_one_geometry.xacro`: `wheel_offset_x` Property vorhanden oder neu anlegen?
- [x] **2.2** Physische Maße prüfen: Abstand Roboter-Mitte → Vorderachse (Mechanik/CAD)
- [x] **2.3** Husarion `rosbot_xl.urdf.xacro` lx/ly als Referenz

### Task 3 — Implementierung
- [x] **3.1** Falls `wheel_offset_x` fehlt: Property mit korrektem Wert anlegen (z.B. `0.113`)
- [x] **3.2** `front_left_wheel_joint` korrigieren (alte Zeile auskommentieren):
  ```xml
  <!-- OLD: <origin xyz="0 ${wheel_offset_y} 0" .../> -->
  <origin xyz="${wheel_offset_x} ${wheel_offset_y} 0" .../>
  ```
- [x] **3.3** `front_right_wheel_joint` analog korrigieren
- [x] **3.4** Hinterrad-Joints prüfen: müssen `−wheel_offset_x` haben (ggf. ebenfalls korrigieren + auskommentieren)

### Task 4 — Controller-YAML abstimmen
- [x] **4.1** `mecanum_my_controllers.yaml`: `sum_of_robot_center_projection_on_X_Y_axis` neu berechnen  
  Formel: `sum = wheel_offset_x + wheel_offset_y`
- [x] **4.2** Alten Wert auskommentieren, neuen Wert darunter einfügen

### Task 5 — Linter & Tests grün
- [x] **5.1** XACRO Syntax: `ament_xmllint src/gubot_one/description/urdf/gubot_one_geometry.xacro`
- [x] **5.2** Tests erneut ausführen → **müssen grün sein**

### Task 6 — Visuelle Verifikation
- [ ] **6.1** Simulation starten, RViz öffnen → TF-Frames prüfen
- [ ] **6.2** `ros2 run tf2_tools view_frames` → TF-Baum als PDF im Workspace speichern (`.vscode/tf_frames.pdf`)
- [ ] **6.3** Symmetrie in Gazebo visuell bestätigen

---

## Betroffene Dateien

- **[NEW]** `src/gubot_one/test/test_urdf_geometry.py`
- **[MODIFY]** `src/gubot_one/description/urdf/gubot_one_geometry.xacro`
- **[MODIFY]** `src/gubot_one/config/mecanum_my_controllers.yaml`

---

## Verifikationskriterium

> pytest grün. TF-Tree zeigt front-Räder bei X=+`wheel_offset_x`, rear-Räder bei X=−`wheel_offset_x`.
