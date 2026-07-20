# Gubot One - Debugging Guide 🐞

Dieser Guide hilft dir, Hardware- und Software-Probleme zu isolieren. Alle Befehle funktionieren sowohl auf dem **Raspberry Pi (via SSH)** als auch auf dem **Remote PC** (sofern die Verbindung steht).

## 1. Quick-Check: Verbindung

Bevor du Hardware testest, prüfe, ob ROS 2 läuft und Topics sichtbar sind.

```bash
ros2 topic list
```

* **Erwartung:** Du siehst eine Liste mit `/cmd_vel`, `/joint_states`, `/arming_controller/commands`, etc.
* **Fehler:** Wenn die Liste leer ist (nur `/rosout`), prüfe Tailscale und die `CYCLONEDDS_URI` Variable.

---

## 2. Basis-Motoren (Fahren) testen 🚗

So bewegst du die Räder direkt, um TwistMux oder Joystick-Probleme zu umgehen.

**Voraussetzung:**

* Akku angeschlossen.
* **STBY-Pin** am Motortreiber auf 3.3V/5V (High).

### Befehl (Fahre geradeaus für 1 Sekunde)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

### Befehl (Drehen auf der Stelle)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.0}}"
```

---

## 3. Nerf-Launcher testen 🔫

Der Launcher wird über **ForwardCommandController** gesteuert. Die Topics erwarten ein Array von Zahlen (`Float64MultiArray`).

### A. System Scharfschalten (Arming)

Der Servo muss den Sicherheitsschalter drücken.

* `1.0` = Scharf (Armed)
* `0.0` = Sicher (Disarmed)

```bash
ros2 topic pub --once /arming_controller/commands std_msgs/msg/Float64MultiArray "{data: [1.0]}"
```

### B. Trigger-Servo (Neigung)

Bewegt den Launcher hoch/runter.

* `6.28` (ca. 2 Pi) = Oben
* `5.23` = Unten

```bash
ros2 topic pub --once /trigger_controller/commands std_msgs/msg/Float64MultiArray "{data: [6.0]}"
```

### C. Flywheels (Motoren)

Startet die beiden Flywheel-Motoren.

* `50.0` = Halbe Kraft
* `100.0` = Volle Kraft
* `0.0` = Stop

```bash
# Starten (Achtung: Laut! 🔊)
ros2 topic pub --once /flywheel_controller/commands std_msgs/msg/Float64MultiArray "{data: [50.0, -50.0]}"

# Stoppen
ros2 topic pub --once /flywheel_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0, 0.0]}"
```

*(Hinweis: Wir senden `[Speed, -Speed]`, da sie gegenläufig drehen müssen!)*

### D. Pusher (Schuss)

Der Servo schiebt den Dart in die Flywheels.

* `15.0` = Feuern (Schnell drehen)
* `0.0` = Stop

```bash
ros2 topic pub --once /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [15.0]}"
```

---

## 4. Sensordaten lesen 📊

### Alle Gelenke & Encoder sehen

Hier siehst du, ob die Encoder zählen (Räder drehen) und wo die Servos stehen.

```bash
ros2 topic echo /joint_states
```

* Achte auf `position` bei `left_wheel_joint` und `right_wheel_joint`. Wenn du die Räder von Hand drehst, müssen sich diese Zahlen ändern!

### Odometrie (Wo glaubt der Roboter zu sein?)

```bash
ros2 topic echo /diff_cont/odom
```

---

## 5. Daten aufzeichnen (Debugging-File) 📼

Wenn ein Fehler nur sporadisch auftritt, zeichne alles auf und analysiere es später.

**Aufnahme starten:**

```bash
# Zeichnet Kommandos und Sensorwerte auf
ros2 bag record -o mein_debug_log /cmd_vel /joint_states /rosout
```

*(Drücke Ctrl+C zum Stoppen)*

**Abspielen (Simulation des Fehlers):**

```bash
ros2 bag play mein_debug_log
```

---

## 6. Logs & Diagnose 📝

### Live-Logs sehen

Wenn ein Node abstürzt oder Fehler wirft:

```bash
ros2 run rqt_console rqt_console
```

*(Nur auf Desktop PC möglich)*

### Log-Dateien auf dem Pi

Wenn der Start fehlschlägt, liegen die Logs hier:

```bash
cd ~/.ros/log/
ls -lt | head  # Zeigt die neuesten Logs
```

---

## Checkliste bei "Nix bewegt sich" 🛑

1. **STBY Pin:** Ist der Pin am Motortreiber auf 3.3V/5V? (Ohne den geht gar nichts!) ⚠️
2. **Akku:** Ist der Motor-Akku voll und angeschlossen? (Der Pi versorgt die Motoren NICHT über USB).
3. **DDS/Netzwerk:**
    * Kannst du vom PC den Pi pingen? `ping 100.67.220.49`
    * Stimmt die `CYCLONEDDS_URI` auf beiden Seiten?
