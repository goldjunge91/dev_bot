# gubot_patrol

Einfacher Patrouillen-Node: fährt ein Quadrat (konfigurierbare Beinlänge
und Geschwindigkeit) und publiziert auf `cmd_vel_nav` (twist_mux-Eingang,
Priorität 10). Über den Service `/patrol_node/set_enabled` (`SetBool`)
lässt sich die Patrouille an-/abschalten; der Status wird auf
`/patrol_node/active` (`Bool`) publiziert.

## Aufbau

| Datei | Inhalt |
|---|---|
| `gubot_patrol/patrol_logic.py` | Pure Zustandsmaschine (kein rclpy): `PatrolParams`, `PatrolPhase`, `advance_phase`, `command_for_phase` |
| `gubot_patrol/patrol_node.py` | ROS-Node: Timer, Publisher, Service — ruft nur die pure Logik |
| `config/patrol_params.yaml` | Default-Parameter |

## Tests

```bash
colcon test --packages-select gubot_patrol
```

| Datei | Ebene | Inhalt |
|---|---|---|
| `test/test_patrol_logic.py` | Pure Unit-Tests | Phasenwechsel, Modulo-Wrap, Kommandos, voller Quadrat-Zyklus |
| `test/test_patrol_node_rclpy.py` | rclpy-Integration | Echter Node + Probe-Node: Timer-Tick publiziert Twist/Bool, Phasenwechsel via rückdatiertem `_phase_start`, Enable/Disable-Service |

Die rclpy-Tests sind deterministisch: der Node-Timer wird gecancelt und
`_on_timer` direkt aufgerufen — kein `sleep`-basiertes Warten.
