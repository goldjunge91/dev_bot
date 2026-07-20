# NERF OS PRO - Modular PlatformIO Edition

Dieses Projekt ist eine modulare Firmware für selbst gebaute Nerf-Dart Launcher Vorrichtung. Der Code basiert auf C++ und nutzt eine Finite State Machine (FSM), um Sicherheit, Schusszyklen und Hardware-Steuerung präzise zu verwalten.

Das Projekt wurde für **PlatformIO** (VS Code / CLion) optimiert und trennt Konfiguration, Logik und Kommunikation sauber voneinander.

## 📂 Projektstruktur

Die Dateistruktur wurde modularisiert, um die Wartbarkeit zu erhöhen.

```text
NERF_MICRO
│
├── include
│   └── Config.h            # ZENTRALE KONFIGURATION
│                           # Hier werden Pins, Timings und Kalibrierungswerte
│                           # definiert. Diese Datei ist global verfügbar.
│
├── lib
│   ├── Control             # KERN-LOGIK (Hardware-Abstraktion)
│   │   ├── FiringFSM.h     # Definition der Zustandsmaschine (State Machine)
│   │   ├── FiringFSM.cpp   # Logik der Zustandsübergänge (Idle, Push, Brake...)
│   │   ├── Launcher.h      # Steuerung von Flywheels (ESCs) & Pusher
│   │   ├── Launcher.cpp    # Implementierung der Hardware-Treiber
│   │   ├── Tilt.h          # Separate Klasse für Neigungsmechanik
│   │   └── Tilt.cpp        # Logik für Tilt-Servos
│   │
│   └── Comms               # KOMMUNIKATION
│       ├── Comms.h         # Header für Serial/UART Parser
│       └── Comms.cpp       # Verarbeitet Befehle von USB & Serial1
│
├── src
│   └── main.cpp            # EINSTIEGSPUNKT
│                           # Initialisiert Objekte und startet den Loop.
│
├── platformio.ini          # PROJEKT-SETTINGS & LIBRARY DEPENDENCIES
└── README.md               # DIESE DATEI

```

## 🚀 Installation & Setup

### Voraussetzungen

* **IDE:** CLion (mit PlatformIO Plugin) oder VS Code (mit PlatformIO Extension).
* **Hardware:** Arduino-kompatibles Board (z.B. Leonardo, Micro, Nano).

## ⚙️ Konfiguration

Alle Anpassungen an der Hardware sollten ausschließlich in der Datei **`include/Config.h`** vorgenommen werden.

* **Pin-Mapping:** Definiert, an welchen Pins ESCs, Servos und Sensoren hängen.
* **Timings:** Schussdauer (`SHOT_DURATION`), Hochlaufzeit (`SPINUP_MS`).
* **Kalibrierung:** Nullpunkte für Servos (`SHOT_NEUTRAL`, `TILT_NEUTRAL`).

## 📡 Serial Command Interface

Der Blaster kann über USB (Serial) oder UART (Serial1) gesteuert werden.
**Baudrate:** 115200

### 1. System & Sicherheit

Grundlegende Befehle für den Status und die Sicherheit des Blasters.

| Befehl | Beschreibung |
| --- | --- |
| `ARM` | **Scharfschalten.** Aktiviert die ESC-Signalausgabe. |
| `DISARM` | **Entschärfen.** Stoppt alle Motoren sofort (Sicherheits-Modus). |
| `STOP` | Not-Aus (Alias für DISARM). |
| `STATUS` | Zeigt den Systemstatus (ARMED / DISARMED) an. |
| `HELP` | Listet alle verfügbaren Befehle auf. |
| `SAVE` | Gibt die aktuelle Konfiguration (Nullpunkte, Timings) auf der Konsole aus. |

### 2. Firing (Schusssteuerung)

Befehle, die direkt mechanische Aktionen auslösen (nur im ARMED-Zustand möglich).

| Befehl | Beschreibung |
| --- | --- |
| `SHOT <val>` | Startet einen kompletten Schusszyklus. `<val>` = Leistung in % (0-100). |
| `TEST_ESC <val>` | Startet **nur** die Flywheels dauerhaft (zum Testen der Motoren). |
| `TEST_SHOT <ms>` | Betätigt **nur** den Pusher (ohne Flywheels). Ideal zum Testen der Mechanik. |

### 3. Tilt (Neigung)

Steuerung der Höhenverstellung.

| Befehl | Beschreibung |
| --- | --- |
| `UP <ms>` | Fährt den Blaster für `ms` Millisekunden nach oben. |
| `DN <ms>` | Fährt den Blaster für `ms` Millisekunden nach unten. |
| `T_POS <us>` | Fährt den Tilt-Servo auf eine absolute Position (500-2500 µs). |
| `TU` / `TD` | "Tilt Up/Down Nudge": Kleine Schritte zur Feinjustierung. |

### 4. Wartung & Setup (Kalibrierung)

**Vorsicht:** Diese Befehle verändern grundlegende Parameter oder starten spezielle Kalibrierungsmodi.

| Befehl | Beschreibung |
| --- | --- |
| `CAL` | **ESC-Kalibrierung.** Startet den Prozess zum Einlernen der ESC-Gaswege (Max -> Min). **Anleitung beachten!** |
| `PWM <us>` | Sendet ein rohes PWM-Signal (Mikrosekunden) an die ESCs (Manuelle Kontrolle). |
| `NF` / `NB` | "Nudge Fwd/Back": Bewegt den Pusher schrittweise vor/zurück (bei Klemmern). |
| `ZERO_S <us>` | Setzt den Nullpunkt (Ruheposition) des **Shot-Servos** (Pusher). |
| `ZERO_T <us>` | Setzt den Nullpunkt (Mittelstellung) des **Tilt-Servos**. |
| `SET_SHOT <ms>` | Definiert die Dauer des Schusszyklus (Pusher-Laufzeit). |

## 🛠 Entwicklungshinweise

1. **Header-Dateien:** Wenn du neue Module erstellst, achte darauf, `.h` (Deklaration) und `.cpp` (Implementierung) zu trennen.
2. **State Machine:** Änderungen an der Schusslogik sollten in `FiringFSM.cpp` erfolgen.
3. **Includes:** Da `Config.h` im `include`-Ordner liegt, kann sie überall mit `#include "Config.h"` eingebunden werden.
