# Plan 04 — `position_proportional_gain` aus Gazebo-xacro entfernen

> [!NOTE]
> **KISS + Workflow:** Minimale Änderung. Alten Parameter auskommentieren (nicht löschen). Kein /tmp.

## Problem

```xml
<!-- ros2_control_gazebo_ign_fortress.xacro — unbekannter Parameter: -->
<param name="position_proportional_gain">20.0</param>
```
`gz_ros2_control/GazeboSimSystem` kennt diesen Parameter nicht → wird still ignoriert.

---

## Tasks

### Task 1 — Test schreiben (TDD: erst fehlschlagend)
- [ ] **1.1** `src/gubot_one/test/test_gazebo_xacro.py` anlegen (oder bestehende Testdatei erweitern)
- [ ] **1.2** Test: XACRO rendern → URDF parsen → `position_proportional_gain` darf im geparsten Output **nicht** erscheinen  
  *(XACRO-Kommentare werden beim Parsen entfernt — Test schlägt fehl solange Parameter aktiv ist)*
- [ ] **1.3** Test ausführen → **muss rot sein**
  ```bash
  colcon test --packages-select gubot_one --pytest-args -k test_gazebo_xacro
  ```

### Task 2 — Implementierung (KISS: eine Zeile)
- [ ] **2.1** `ros2_control_gazebo_ign_fortress.xacro` — Parameter auskommentieren:
  ```xml
  <!-- OLD: ignorierter Parameter — gz_ros2_control/GazeboSimSystem kennt ihn nicht -->
  <!-- <param name="position_proportional_gain">20.0</param> -->
  ```
- [ ] **2.2** Sicherstellen dass kein leerer Block entsteht (ggf. sinnvollen Kommentar einfügen)

### Task 3 — Linter & Tests grün
- [ ] **3.1** `ament_xmllint src/gubot_one/description/urdf/ros2_control_gazebo_ign_fortress.xacro`
- [ ] **3.2** Tests erneut ausführen → **müssen grün sein**
- [ ] **3.3** Simulation kurz starten → kein Warning über unbekannte Parameter in Console

---

## Betroffene Dateien

- **[NEW]** `src/gubot_one/test/test_gazebo_xacro.py` *(oder Erweiterung bestehender Testdatei)*
- **[MODIFY]** `src/gubot_one/description/urdf/ros2_control_gazebo_ign_fortress.xacro`

---

## Verifikationskriterium

> pytest grün. Simulation startet ohne Warning zu `position_proportional_gain`.

> [!NOTE]
> Diese Aufgabe hat **kein funktionales Risiko** — eignet sich als Einstieg für TDD-Übung im Projekt.
