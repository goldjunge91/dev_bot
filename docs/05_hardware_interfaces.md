# Phase 5: Interaktion mit der Welt (Hardware Interfaces / C++)

Dein Roboter hat echte C++ Plugins, um mit Hardware zu reden. Konkret schauen wir uns `nerf_system.cpp` und `diffbot_system.cpp` an.
Diese Plugins erben von `hardware_interface::SystemInterface`. Das ist die Blaupause für `ros2_control`, das offizielle Roboter-Controller-Modul in ROS 2.

## 1. Wie arbeitet ros2_control? (Der Lifecycle)
Ein Hardware-Interface ist komplizierter als ein normaler Node. Es hat einen festen Lebenszyklus (Lifecycle). `ros2_control` ruft nacheinander ganz bestimmte Funktionen in deiner C++ Klasse auf:

1. `on_init()`: Das allererste, was beim Systemstart passiert. C++ schaut in die URDF, liest Config-Parameter (welcher Port? Welche Baudrate?) und merkt sich die Pointers zu den Gelenken.
2. `on_configure()`: Hier wird ernst gemacht. In deiner `DiffDriveArduinoHardware::on_configure` steht z.B.: `comms_.connect(cfg_.device, cfg_.baud_rate, cfg_.timeout_ms);`. Er öffnet hier die serielle Verbindung zum Arduino.
3. `on_activate()`: Das System meldet sich bereit.
4. **Die Endlosschleife (`read()` und `write()`)**: Wenn alles okay ist, ruft ROS 2 diese beiden Funktionen nun hunderte Male pro Sekunde hintereinander auf.

## 2. State vs. Command Interfaces
Motorsteuerungen in ROS 2 funktionieren über geteilte Plätze im Arbeitsspeicher.
- **State Interfaces:** *Lese-Rechte*. Der Encoderwert des echten Rades.
- **Command Interfaces:** *Schreib-Rechte*. Die Wunschgeschwindigkeit vom ROS Navigations-Node.

Beim Starten verknüpft dein C++ Code seine eigenen C++ Variablen mit `ros2_control`:
```cpp
// Beispiel aus diffbot_system.cpp
state_interfaces.emplace_back(hardware_interface::StateInterface(
    wheel_l_.name, hardware_interface::HW_IF_POSITION, &wheel_l_.pos));
```
*Deutsch:* "Trage das `Position` Lese-Interface für das linke Rad ein. Den echten Wert dazu findest du in Zukunft direkt an der Speicheradresse `&wheel_l_.pos` in meinem Code." (Das kaufmännische Und `&` bedeutet in C++: Gib mir die Speicheradresse / den Pointer).

## 3. Der `read()` Loop (Hardware → Sensoren)
Hundertmal pro Sekunde will ROS 2 wissen: "Wo stehen die Sensoren?". Das passiert im `read()`.

```cpp
hardware_interface::return_type diffdrive_arduino::read(...) {
    // 1. Hole Werte via Serielle Schnittstelle vom Arduino
    comms_.read_encoder_values(wheel_l_.enc, wheel_r_.enc);

    // 2. Errechne radiale Position (Winkel) aus wilden rohen Encoder-Ticks
    wheel_l_.pos = wheel_l_.calc_enc_angle();
    // [...]
    return hardware_interface::return_type::OK;
}
```
*Wichtig hier:* Sobald `wheel_l_.pos` aktualisiert ist, hat ROS 2 diesen Wert in der gleichen Millisekunde, weil der Pointer von oben (die `&wheel_l_.pos`) darauf verweist! Alles ist über direkten Speicher verlinkt, das macht `ros2_control` unfassbar schnell.

## 4. Der `write()` Loop (Kommandos → Hardware)
Nach dem Lesen berechnet ROS 2, wie schnell der Motor eigentlich drehen sollte. Der errechnete Wunschwert landet in den Command-Positionen (z.B. in `wheel_l_.cmd`). Das nächste, was aufgerufen wird, ist `write()`, wo DU diesen Wunsch in echte Hardware umwandeln musst.

Schauen wir uns das Nerf System an (`nerf_system.cpp`):
```cpp
hardware_interface::return_type NerfSystem::write(...) {
    // 1. Wurde vom Controller gefordert zu schießen? (>0)
    int shot_power = static_cast<int>(hw_commands_.shooter_pos);
    
    // 2. Wenn ja, und wir aktuell nicht schießen, sende den seriellen Befehl.
    if (shot_power > 0 && !pusher_active_) {
        std::stringstream shot_ss;
        shot_ss << "SHOT " << shot_power;   // Baut den Textstring "SHOT 100"
        
        comms_.send_command(shot_ss.str()); // Schickt es über USB an den Firmware-Arduino
        pusher_active_ = true;              // Verhindert Spamming
    } 
    // ...
    return hardware_interface::return_type::OK;
}
```

## Zusammenfassung Architektur
Du hast also die perfekte Architektur:
1. Der **Arduino (Firmware)** redet über USB "Text" (z.B. `SHOT 100` oder `UP 500`).
2. Das **Hardware Interface (C++)** ist der schnelle Übersetzer, der über USB diese Textstrings schickt.
3. Die **Controller (Controller Manager)** wissen nichts von USB oder Text. Sie kennen nur `shooter_pos`.
4. Der **Python Joystick Node (`nerf_joy.py`)** weiß nichts von der Hardware. Er klickt Tastendrücke an und published `/shooter_controller/commands`.
