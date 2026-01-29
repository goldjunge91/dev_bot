# ROSArduinoBridge - TB6612 Version

Arduino Firmware für `diffdrive_arduino` ROS 2 Hardware Interface.

> Basiert auf [ros_arduino_bridge von Josh Newans](https://github.com/joshnewans/ros_arduino_bridge)

## Änderungen für TB6612

Diese Version wurde für den **TB6612FNG** Motor Driver angepasst (statt L298N).

## Verkabelung

### TB6612 → Arduino Nano

```
TB6612          Arduino Nano
──────          ────────────
VCC      ────►  5V
GND      ────►  GND
STBY     ────►  5V (immer aktiv)
PWMA     ────►  D3 (PWM)
AIN1     ────►  D4
AIN2     ────►  D5
PWMB     ────►  D9 (PWM)
BIN1     ────►  D7
BIN2     ────►  D8
VM       ────►  Motor-Akku (6-12V)
AO1/AO2  ────►  Motor Links
BO1/BO2  ────►  Motor Rechts
```

### Encoder → Arduino Nano

```
Encoder Links           Arduino Nano
─────────────           ────────────
A        ────►          D2 (PORTD2)
B        ────►          D3 (PORTD3)
VCC      ────►          5V
GND      ────►          GND

Encoder Rechts          Arduino Nano
──────────────          ────────────
A        ────►          A4 (PORTC4)
B        ────►          A5 (PORTC5)
VCC      ────►          5V
GND      ────►          GND
```
### TB6612 Motor Driver

| TB6612 | Arduino Nano | Pi Pico |
|--------|--------------|---------|
| VCC | 5V | 3.3V |
| GND | GND | GND |
| STBY | 5V | 3.3V |
| PWMA | D3 | GP3 |
| AIN1 | D4 | GP4 |
| AIN2 | D5 | GP5 |
| PWMB | D9 | GP9 |
| BIN1 | D7 | GP7 |
| BIN2 | D8 | GP8 |
| VM | Motor-Akku | Motor-Akku |

### Encoder

| Encoder | Arduino Nano | Pi Pico |
|---------|--------------|---------|
| Links A | D2 | GP2 |
| Links B | D3 | GP3 |
| Rechts A | A4 | GP4 |
| Rechts B | A5 | GP5 |

> ⚠️ **Achtung Pi Pico:** Pins können in `encoder_driver.h` angepasst werden!

---

## Installation

### Arduino Nano

1. Arduino IDE öffnen
2. Board: **Arduino Nano**
3. Prozessor: **ATmega328P** (oder Old Bootloader)
4. `ROSArduinoBridge.ino` öffnen und hochladen

### Raspberry Pi Pico

1. [arduino-pico Core installieren](https://github.com/earlephilhower/arduino-pico)
   - In Arduino IDE: File → Preferences
   - Additional Board URLs: `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json`
   - Tools → Board → Board Manager → "pico" suchen → installieren
2. Board: **Raspberry Pi Pico**
3. `ROSArduinoBridge.ino` öffnen und hochladen

---

## Serial Befehle (57600 Baud)

| Befehl | Beschreibung |
|--------|--------------|
| `e` | Encoder-Werte lesen |
| `r` | Encoder zurücksetzen |
| `o 100 100` | Motoren mit PWM steuern (roh) |
| `m 10 10` | Geschwindigkeitsregelung (PID) |

## ROS 2 Parameter

In `ros2_control.xacro`:

```xml
<param name="device">/dev/ttyUSB0</param>  <!-- oder /dev/ttyACM0 -->
<param name="baud_rate">57600</param>
<param name="enc_counts_per_rev">XXXX</param>
```

**enc_counts_per_rev berechnen:**
```
<!-- Encoder_PPR × Getriebe × 4 -->
enc_counts_per_rev = Encoder_PPR × Getriebe × 4
```
---

## Anpassungen

### Motor-Pins ändern
Bearbeite `motor_driver.h`:
```cpp
#define LEFT_MOTOR_PWM    3   // Ändere nach Bedarf
```

### Encoder-Pins ändern (nur Pi Pico)
Bearbeite `encoder_driver.h`:
```cpp
#define LEFT_ENC_PIN_A  2   // Ändere nach Bedarf
```


<!-- Ab hier nichts ändern  -->

# Arduino Motor Controller

This code turns an Arduino into a motor controller!
It provides a simple serial interface to communicate with a high-level computer (e.g. running ROS), and generates the appropriate PWM signals for a motor driver, to drive two motors.

This is a fork of the original code, with some changes, and removal of the ROS nodes (see [this repo](https://github.com/joshnewans/serial_motor_demo) for an alternative). Check out `README-orig.md` for the original README.

As I only have need for a subset of the functionality, I have no idea what does and doesn't work, beyond what is detailed below.
Feedback/improvements are welcome (though no promises on how quickly I'll respond). I currently only use the L298N driver, and the Arduino encoder mode.



TODO
- Finish this README


## Functionality

The main functionality provided is to receive motor speed requests over a serial connection, and provide encoder feedback.
The original code has provisions for other features - e.g. read/write of digital/analog pins, servo control, but I've never used them.

The main commands to know are

- `e` - Motor responds with current encoder counts for each motor
- `r` - Reset encoder values
- `o <PWM1> <PWM2>` - Set the raw PWM speed of each motor (-255 to 255)
- `m <Spd1> <Spd2>` - Set the closed-loop speed of each motor in *counts per loop* (Default loop rate is 30, so `(counts per sec)/30`
- `p <Kp> <Kd> <Ki> <Ko>` - Update the PID parameters


## Gotchas

Some quick things to note

- There is an auto timeout (default 2s) so you need to keep sending commands for it to keep moving
- PID parameter order is PDI (?)
- Motor speed is in counts per loop
- Default baud rate 57600
- Needs carriage return (CR)
- Make sure serial is enabled (user in dialout group)
- Check out the original readme for more


## TODO (maybe)
- Document PID tuning
- Make the speed input counts per second
- Add/test more driver boards
- Add/test other functionality