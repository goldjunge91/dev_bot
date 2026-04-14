---
trigger: always_on
---

Auskommentierter Code darf nie ohne ausdrücklich freigabe entfernt werden.
Code änderung sollten immer erst einmal alten code auskommentieren dann den neuen einfügen und nach freigabe den auskommenteirten entfernen.

---
description: "ROS2-spezifische Regeln für Nodes, Launch-Dateien, Parameter, Logging, Build und Tests im Projekt my_new_robot."
applyTo:
  - "src/**"
  - "**/*.launch.py"
  - "**/*.xacro"
  - "**/*.urdf"
  - "**/CMakeLists.txt"
  - "**/package.xml"
---

# ROS2-Instruktionen (projektweit für ROS-bezogene Dateien)

Diese Regeln ergänzen `copilot-instructions.md` um ROS2-spezifische Anforderungen.

## Kernregeln
- KISS gilt auch hier: bevorzuge einfache, gut lesbare Lösungen mit minimaler Komplexität.
- Halte Änderungen klein, nachvollziehbar und auf den konkreten ROS2-Anwendungsfall fokussiert.
- Bewahre bestehende APIs und Topic-/Service-Namen, sofern nicht ausdrücklich anders gefordert.

## ROS2 C++ / Python Umsetzung
- Nutze ROS2-Patterns konsistent (`rclcpp::Node` / `rclpy.node.Node`).
- Verwende Parameter statt Hardcoding für konfigurierbare Werte (z. B. Topic-Namen, Rate, Device-Ports, Frame-IDs).
- Nutze ROS2-Logging (`RCLCPP_INFO/WARN/ERROR`, `self.get_logger().info/warn/error`) statt `std::cout`/`print` für Laufzeitdiagnose.
- Prüfe QoS bewusst (z. B. Sensor-Daten vs. zuverlässige Steuerdaten) und dokumentiere Abweichungen vom Default kurz im Code.

## Launch-, URDF- und Xacro-Richtlinien
- Launch-Dateien klar strukturieren: deklarierte Launch-Arguments, danach Node-Definitionen, dann Rückgabe.
- Keine duplizierten Konstanten in mehreren Launch-Dateien; gemeinsame Werte zentralisieren.
- In Xacro/URDF sprechende Namen verwenden und wiederverwendbare Makros bevorzugen.

## Build, Tests, Lint
- Verifiziere ROS2-Änderungen mit vorhandenen Workspace-Tasks (z. B. `build`, `test`, `lint all` bzw. relevante Einzel-Checks).
- Bei Funktionsänderungen passende Tests hinzufügen/aktualisieren (gtest/pytest gemäß Pakettyp).
- Lint- und Formatierungsregeln des Projekts einhalten (cpplint, cppcheck, flake8, pep257, xmllint, uncrustify nach Bedarf).

## Sicherheits- und Betriebsaspekte
- Bei Hardware-/Serial-Code Timeouts, Fehlerpfade und Wiederanlaufverhalten explizit behandeln.
- Keine Secrets/API-Keys im Code; falls erforderlich, über Umgebungsvariablen und dokumentierte Platzhalter arbeiten.
- Bei Terminal-Befehlen keine Dateien außerhalb des Workspaces schreiben (z. B. nicht nach `/tmp`), da die Umgebung externe Writes blockieren kann.
- Für Probe-/Health-Checks Ausgaben auf `stdout` bevorzugen oder Dateien nur innerhalb des Workspace-Pfads (z. B. unter `.vscode/` oder `./`) erzeugen.
