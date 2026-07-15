## Test‑Kommandos für Simulation & ros2_control ✅

Commands mit um Simulation + Controller‑Status zu prüfen.

---

## Simulation starten (Gubot + Nerf im Sim)

```bash
ros2 launch gubot_gazebo simulation.launch.py
```

Nerf‑Launcher-Sim starten:

```bash
ros2 launch nerf_standalone simulate.launch.py
```

---

## ros2_control Status prüfen
### Hardware‑Interfaces
```bash
ros2 control list_hardware_interfaces
```

### Controller‑Status
```bash
ros2 control list_controllers
```

---

## Controller gezielt prüfen

Beispiel: Trigger‑Position setzen  
```bash
ros2 topic pub /trigger_controller/commands std_msgs/msg/Float64MultiArray "{data: [6.0]}"
```

Flywheel‑Geschwindigkeit setzen  
```bash
ros2 topic pub /flywheel_controller/commands std_msgs/msg/Float64MultiArray "{data: [50.0, 50.0]}"
```

Pusher (Schuss)  
```bash
ros2 topic pub /pusher_controller/commands std_msgs/msg/Float64MultiArray "{data: [2.0]}"
```

Arming aktivieren  
```bash
ros2 topic pub /arming_controller/commands std_msgs/msg/Float64MultiArray "{data: [1.0]}"
```

---

## Typische Checks zur Fehlersuche
```bash
ros2 control list_controller_types
```

```bash
ros2 node list
```

```bash
ros2 topic list
```
