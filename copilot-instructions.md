---
name: copilot-instructions
description: "Projektweite Regeln und Vorgaben für das Repository 'my_new_robot'."
applyTo: ["**"]
---

# Projekt- / Workspace-Instruktionen

Dieses Dokument fasst die projektweiten Konventionen und Verifikationsschritte zusammen, die der Copilot-Agent und Beitragende einhalten sollen.

## Kernaussagen (durchgesetzt)
- Test-Driven Development (TDD): Jeder Fix oder neue Funktion hat zuerst einen fehlschlagenden Test. Erst wenn der Test existiert, wird die Implementierung geschrieben. Aufgabe gilt erst als erledigt, wenn der Test grün ist.
- KISS-Prinzip: Halte Lösungen so einfach wie möglich. Bevorzuge die kleinste verständliche Änderung mit minimaler Komplexität und ohne unnötige Abstraktionen.
- Verifikation: Verwende vorhandene Test-Tasks (`./test.sh`, `ament_*` Targets). CI-Checks müssen lokal reproduzierbar sein.
- Codeänderungen: Beim Ersetzen von Code: kommentiere den bisherigen Block aus und füge den neuen Code direkt darunter ein. Kommentierter Code bleibt, bis explizite Zustimmung zur Entfernung vorliegt.
- Terminal-/Agent-Commands dürfen keine Dateien außerhalb des Workspace schreiben (z. B. nicht nach `/tmp`), weil die Umgebung solche Writes blockieren kann.
- Für Probe-/Health-Checks bevorzugt `stdout` verwenden oder nur innerhalb des Workspace-Pfads schreiben (z. B. `.vscode/`, `./`).

## Codestandards (ROS2 / C++ / Python)
- Namenskonventionen: Klassen `PascalCase`, Funktionen/Variablen `snake_case`, Konstanten `SCREAMING_SNAKE_CASE`, Dateinamen `snake_case`.
- Moderne C++/ROS2: RAII, smart pointers (`std::unique_ptr` / `std::shared_ptr`), Standard-Container bevorzugen.
- Logging: Nutze ROS2 Logging-Makros (`RCLCPP_INFO`, `RCLCPP_ERROR`, ...). Nutze strukturierte (JSON-artige) Payloads für Observability.

## Änderungs-Workflow
1. Schreibe einen fehlschlagenden Test (gtest für C++, pytest für Python).
2. Implementiere Änderung, halte dich an Naming- und Stilregeln.
3. Führe Tests lokal aus und stelle sicher, dass alle relevanten Linter/Checks grün sind.
4. Kommentiere alten Code aus und füge neuen Code direkt darunter ein (siehe oben).

## Tests & Linter
- C++: `gtest` via `ament_cmake_gtest`.
- Python: `pytest` via `ament_add_pytest_test`.
- Linter: `ament_lint_common` (flake8, cpplint, cppcheck, pep257, xmllint, uncrustify nach Bedarf).

## Dateiposition & Anwendung
- Dateiname: `copilot-instructions.md` im Projekt-Root (workspace-wide). Diese Datei wird als immer geladene Workspace-Anweisung behandelt.
- Wenn Regeln nur für bestimmte Dateien gelten sollen, bitte explizit `applyTo` anpassen (z. B. `src/**`, `**/*.py`). Vermeide `applyTo: ["**"]` nur wenn wirklich global gewünscht.

## Hinweise für den Agenten / Contributors
- Vor größeren Änderungen prüfen, ob eine `.env` benötigt wird; falls nicht vorhanden, lege eine `.env` mit Platzhaltern an und weise darauf hin.
- Bei unsicheren Fällen kurze Rückfrage an den Reviewer (z. B. ob Rückwärtskompatibilität erforderlich ist).

## Beispiele für Prompts
- "Erzeuge einen fehlschlagenden `gtest` für die Klasse `DiffDriveController` und implementiere minimalen Fix, damit der Test besteht." 
- "Refaktoriere `serial_node.cpp`: behalte API, kommentiere alten Code aus, füge neue Implementierung hinzu und füge `gtest`-Abdeckung hinzu."

## Nächste Schritte / Iteration
- Wenn etwas unklar ist (Scope, Dateitypen, harte Regel vs. Präferenz), antworte auf diese Datei mit konkreten Präzisierungen. Ich (der Agent) werde die Datei entsprechend aktualisieren.

---
Legende: Diese Instruktionen sind bewusst präskriptiv — bitte Rückmeldung, welche Teile hart durchgesetzt werden sollen und welche nur als Guideline gelten.
