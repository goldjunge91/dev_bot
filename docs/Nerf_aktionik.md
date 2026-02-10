# Nerf-Aktorik – Test- & Diagnoseplan

Stand: 2026-02-10

## Ziel
Gezielte Prüfung der Nerf-Aktorik (Tilt + Pusher/Shot) inklusive serieller Kommunikation, sicherem Betrieb und reproduzierbaren Tests.

## Voraussetzungen
- Roboter im sicheren Zustand (mechanisch frei, keine Personen in Reichweite).
- Nerf-System stromversorgt, Servos korrekt angeschlossen.
- Arduino Leonardo sichtbar als:
  - `/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00`
- Diffdrive Pico sichtbar als:
  - `/dev/serial/by-id/usb-Raspberry_Pi_Pico_50443405786ACA1C-if00`

## Sicherheitsregeln
- Vor jedem Aktortest: **ARM** nur bei freier Mechanik.
- Bei unkontrollierter Bewegung: **DISARM** sofort.
- Tilt zuerst in kleinen Schritten bewegen (keine Endanschläge rammen).

---

## 1) Serielle Verbindung prüfen (Arduino)

### Command
- Öffnen des Monitors (existierender Flow):
  - `screen /dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00 115200`

### Erwartete Eingaben
- `ARM`
- `DISARM`
- `TEST_SHOT`
- `ZERO_T`
- `NB` / `NF` / `up` / `dn`

### Zu prüfen (Messages)
- Keine STATUS‑Interaktion erwartet (Befehl ist seriell nicht aktiv).
- Klare ACK/State-Ausgaben nach `ARM`/`DISARM`.
- Plausible Rückmeldung auf `UP/DN` und `ZERO_T`.

---

## 2) Tilt‑Aktuator einzeln testen

### Ziel
Sicherstellen, dass Tilt auf definierte Geschwindigkeiten reagiert, nicht unkontrolliert durchläuft und sauber stoppt.

### Commands (nacheinander)
1. `DISARM`
2. `ZERO_T 1500`
3. `UP 200`
4. `DN 200`
5. `UP 200`
6. `DN 200`
7. `DISARM`

### Checks
- Tilt bewegt sich auch ohne `ARM` (aktueller Firmware‑Stand).
- **Kontinuierlicher Servo:** `UP/DN <ms>` ist der bevorzugte Weg (zeitgesteuert).
- Neutralpunkt (`ZERO_T 1500`) erzeugt Stopp (keine Bewegung).
- Bei `DISARM` sofortiger Stopp.

### Aktueller Befund (2026-02-10)
- `ZERO_T` funktioniert ohne `ARM`.
- Tilt ist **kontinuierlicher Servo** → Steuerung bevorzugt über zeitbegrenzte `UP/DN`.
- Empfehlung: **nur `UP/DN` verwenden**, um zeitlich begrenzte Bewegungen zu erzwingen.
- `UP/DN` funktionieren und stoppen sauber nach der Zeit.
- Beobachtung: `UP 360` meldet aktuell **200 ms** (möglicher Argument‑Parsing/Handling‑Hinweis).
 - `T_POS` ist in der Firmware deaktiviert.

---

## 3) Pusher/Shot‑Aktuator einzeln testen

### Ziel
Pusher/Shot Servo reagiert sichtbar und zuverlässig.

### Commands
1. `DISARM`
2. `ARM`
3. `TEST_SHOT` (mehrfach, 3–5 Mal)
4. `DISARM`

### Checks
- Servo bewegt sich sichtbar (Pusher).
- Keine Bewegung ohne ARM.
- Wiederholbarkeit ohne Aussetzer.

---

## 4) Host‑Seite (ROS) prüfen

### Relevante Files
- `src/nerf_standalone/hardware/nerf_system.cpp`
- `src/nerf_standalone/hardware/Comms.h`
- `src/nerf_standalone/hardware/Comms.cpp` (falls vorhanden)

### ROS Commands
- Launch (falls vorhanden; ggf. anpassen):
  - `ros2 launch nerf_standalone <dein_launch>.launch.py`
- Nodes prüfen:
  - `ros2 node list`
- Topics prüfen:
  - `ros2 topic list | grep -i nerf`
- Services prüfen:
  - `ros2 service list | grep -i nerf`

### Checks
- `ros2_control_node` läuft stabil (keine Serial‑I/O‑Crashes).
- Nerf‑Hardware‑Interface meldet READY/ARM‑State korrekt.
- Bei Disconnect: frühe Rückgabe im Interface greift (kein Crash).

---

## 5) Logs sammeln (falls Fehler)

### Commands
- `journalctl -u ros2` (falls Service genutzt)
- `ros2 topic echo /rosout | grep -i nerf`

### Checks
- Serial‑Fehler werden abgefangen, keine ungefangenen Exceptions.

---

## 6) Gezielter Build

### Command (nur nerf_standalone)
- `colcon build --packages-select nerf_standalone`

### Checks
- Build endet ohne Fehler.

---

## Offene Punkte
- Falls Tilt weiterläuft: PWM‑Grenzen & Servo‑Typ prüfen.
- Falls Pusher nicht reagiert: Servo‑Pin, Stromversorgung, Signal (PWM) prüfen.
- Falls STATUS später wieder benötigt: Filter‑Logik in `Comms.h` und Parser prüfen.
