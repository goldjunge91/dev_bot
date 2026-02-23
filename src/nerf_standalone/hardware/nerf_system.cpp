// Implementierung der Nerf Hardware-Schnittstelle für ROS2 Control
// Verwaltet serielle Kommunikation mit Arduino und Hardware-Interfaces
#include "nerf_standalone/nerf_system.hpp"

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/logging.hpp"

#include <cmath>
#include <sstream>
#include <vector>

namespace nerf_standalone {

// --- NerfComms Implementierung (Serielle Kommunikation) ---

void NerfComms::connect(const std::string &serial_device, int32_t baud_rate) {
    // Baudrate konvertieren (Standard-Werte für Arduino-Kommunikation)
    LibSerial::BaudRate baud;
    switch (baud_rate) {
        case 9600:
            baud = LibSerial::BaudRate::BAUD_9600;  // Langsam, für Debugging
            break;
        case 57600:
            baud = LibSerial::BaudRate::BAUD_57600;  // Mittel
            break;
        case 115200:
            baud = LibSerial::BaudRate::BAUD_115200;  // Standard für Arduino
            break;
        default:
            baud = LibSerial::BaudRate::BAUD_115200;  // Fallback
            break;
    }

    serial_conn_.Open(serial_device);  // Öffne serielle Verbindung (z.B. /dev/ttyACM0)
    serial_conn_.SetBaudRate(baud);    // Setze Übertragungsrate
    serial_conn_.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);    // 8 Datenbits
    serial_conn_.SetFlowControl(LibSerial::FlowControl::FLOW_CONTROL_NONE);  // Keine Flusskontrolle
    serial_conn_.SetParity(LibSerial::Parity::PARITY_NONE);                  // Keine Parität
    serial_conn_.SetStopBits(LibSerial::StopBits::STOP_BITS_1);              // 1 Stoppbit
}

void NerfComms::disconnect() {
    if (serial_conn_.IsOpen()) {  // Prüfe ob Verbindung offen ist
        try {
            serial_conn_.Close();  // Schließe serielle Verbindung sauber
        } catch (const std::exception &e) {
            RCLCPP_ERROR(
                rclcpp::get_logger("NerfComms"), "Error closing serial port: %s", e.what());
        }
    }
}

bool NerfComms::connected() const {
    return serial_conn_.IsOpen();
}  // Status der Verbindung

void NerfComms::send_command(const std::string &cmd) {
    if (!serial_conn_.IsOpen())  // Keine Verbindung -> Abbruch
        return;

    try {
        // Füge Newline für Arduino hinzu (Arduino erwartet Zeilenende als Befehlstrenner)
        serial_conn_.Write(cmd + "\n");
        // serial_conn_.DrainWriteBuffer(); // Optional: Warte bis Daten gesendet wurden
    } catch (const std::exception &e) {
        RCLCPP_ERROR(
            rclcpp::get_logger("NerfComms"), "Serial write failed (%s). Closing port.", e.what());
        disconnect();  // Bei Fehler Verbindung schließen
    }
}

// --- NerfSystem Implementierung (Haupt-Hardware-Interface) ---

hardware_interface::CallbackReturn NerfSystem::on_init(
    const hardware_interface::HardwareInfo &info) {
    // Basis-Initialisierung durchführen
    if (hardware_interface::SystemInterface::on_init(info) !=
        hardware_interface::CallbackReturn::SUCCESS) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    // Parameter aus URDF/YAML lesen
    port_ = info_.hardware_parameters["port"];  // Serieller Port (z.B. /dev/ttyACM0)
    baud_rate_ = std::stoi(info_.hardware_parameters["baud_rate"]);  // Baudrate (z.B. 115200)

    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "Initialized NerfSystem on port %s @ %d",
                port_.c_str(),
                baud_rate_);

    // Verifiziere Gelenke (Joints) aus URDF-Konfiguration
    for (const hardware_interface::ComponentInfo &joint : info_.joints) {
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Joint found: %s", joint.name.c_str());

        // Prüfe ob Gelenk unterstützt wird (nur Nerf-spezifische Gelenke erlaubt)
        if (joint.name != "trigger_joint" &&         // Neigung/Tilt-Servo
            joint.name != "dart_pusher_joint" &&     // Dart-Schieber
            joint.name != "flywheel_left_joint" &&   // Linkes Schwungrad
            joint.name != "flywheel_right_joint" &&  // Rechtes Schwungrad
            joint.name != "system_arming_joint") {   // Arming-Schalter
            RCLCPP_FATAL(
                rclcpp::get_logger("NerfSystem"), "Unsupported joint '%s'", joint.name.c_str());
            return hardware_interface::CallbackReturn::ERROR;
        }

        // Prüfe Command-Interfaces (Position oder Velocity)
        for (const auto &command_interface : joint.command_interfaces) {
            if (!get_command_ptr(joint.name, command_interface.name)) {
                RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                             "Unsupported command interface '%s' for joint '%s'",
                             command_interface.name.c_str(),
                             joint.name.c_str());
                return hardware_interface::CallbackReturn::ERROR;
            }
        }

        // Prüfe State-Interfaces (Position und Velocity Feedback)
        for (const auto &state_interface : joint.state_interfaces) {
            if (!get_state_ptr(joint.name, state_interface.name)) {
                RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                             "Unsupported state interface '%s' for joint '%s'",
                             state_interface.name.c_str(),
                             joint.name.c_str());
                return hardware_interface::CallbackReturn::ERROR;
            }
        }
    }

    return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> NerfSystem::export_state_interfaces() {
    // Exportiere State-Interfaces für ROS2 Control (Feedback-Werte)
    std::vector<hardware_interface::StateInterface> state_interfaces;

    for (const auto &joint : info_.joints) {
        for (const auto &interface : joint.state_interfaces) {
            double *state_ptr =
                get_state_ptr(joint.name, interface.name);  // Hole Zeiger auf State-Variable
            if (!state_ptr) {
                RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                             "Skipping unsupported state interface '%s' for joint '%s'",
                             interface.name.c_str(),
                             joint.name.c_str());
                continue;
            }
            // Erstelle State-Interface (z.B. trigger_joint/position)
            state_interfaces.emplace_back(
                hardware_interface::StateInterface(joint.name, interface.name, state_ptr));
        }
    }

    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> NerfSystem::export_command_interfaces() {
    // Exportiere Command-Interfaces für ROS2 Control (Sollwerte)
    std::vector<hardware_interface::CommandInterface> command_interfaces;

    for (const auto &joint : info_.joints) {
        for (const auto &interface : joint.command_interfaces) {
            double *command_ptr =
                get_command_ptr(joint.name, interface.name);  // Hole Zeiger auf Command-Variable
            if (!command_ptr) {
                RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                             "Skipping unsupported command interface '%s' for joint '%s'",
                             interface.name.c_str(),
                             joint.name.c_str());
                continue;
            }
            // Erstelle Command-Interface (z.B. trigger_joint/position)
            command_interfaces.emplace_back(
                hardware_interface::CommandInterface(joint.name, interface.name, command_ptr));
        }
    }

    return command_interfaces;
}

hardware_interface::CallbackReturn NerfSystem::on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    // Lifecycle: Configure - Öffne serielle Verbindung zum Arduino
    RCLCPP_INFO(
        rclcpp::get_logger("NerfSystem"), "Configuring... Opening Serial %s", port_.c_str());
    try {
        comms_.connect(port_, baud_rate_);  // Verbinde mit Arduino
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Serial Connected Successfully");
    } catch (const std::exception &e) {
        RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"), "Failed to open serial port: %s", e.what());
        return hardware_interface::CallbackReturn::ERROR;
    }
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_cleanup(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    // Lifecycle: Cleanup - Schließe serielle Verbindung
    comms_.disconnect();
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    // Lifecycle: Activate - System bereit (kein Auto-Arming aus Sicherheitsgründen)
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System Activated (Waiting for ARM command)");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    // Lifecycle: Deactivate - Sicherheitsstopp und Disarm
    comms_.send_command("TEST_ESC 0");  // Stoppe Schwungräder
    comms_.send_command("DISARM");      // Deaktiviere System
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System DISARMED");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type NerfSystem::read(const rclcpp::Time & /*time*/,
                                                 const rclcpp::Duration & /*period*/) {
    // Lese Hardware-Status (Open-Loop: Spiegle Commands in States)
    // Schütze gegen NaN/Inf-Werte von Controllern durch Validierung
    auto safe_copy = [](double src, double &dst) {
        if (std::isfinite(src)) {  // Prüfe ob Wert gültig ist
            dst = src;
        } else {
            dst = dst;  // Behalte vorherigen Wert bei ungültiger Eingabe
        }
    };

    // Kopiere Command-Werte in State-Werte (Open-Loop Feedback)
    safe_copy(hw_commands_.trigger_pos, hw_states_.trigger_pos);  // Trigger Position
    hw_states_.trigger_vel = 0.0;                                 // Trigger Velocity (immer 0)
    safe_copy(hw_commands_.pusher_vel, hw_states_.pusher_vel);    // Pusher Velocity
    safe_copy(hw_commands_.flywheel_l_vel, hw_states_.flywheel_l_vel);  // Linkes Schwungrad
    safe_copy(hw_commands_.flywheel_r_vel, hw_states_.flywheel_r_vel);  // Rechtes Schwungrad
    safe_copy(hw_commands_.arming_pos, hw_states_.arming_pos);          // Arming Position

    // Finale Sicherheitsprüfung: Stelle sicher dass keine States NaN/Inf enthalten
    auto sanitize = [](double &v) {
        if (!std::isfinite(v)) v = 0.0;  // Setze auf 0 bei ungültigem Wert
    };
    sanitize(hw_states_.trigger_pos);
    sanitize(hw_states_.trigger_vel);
    sanitize(hw_states_.pusher_pos);
    sanitize(hw_states_.pusher_vel);
    sanitize(hw_states_.flywheel_l_pos);
    sanitize(hw_states_.flywheel_l_vel);
    sanitize(hw_states_.flywheel_r_pos);
    sanitize(hw_states_.flywheel_r_vel);
    sanitize(hw_states_.arming_pos);
    sanitize(hw_states_.arming_vel);
    return hardware_interface::return_type::OK;
}

hardware_interface::return_type NerfSystem::write(const rclcpp::Time & /*time*/,
                                                  const rclcpp::Duration & /*period*/) {
    // Schreibe Commands an Hardware (Arduino via Serial)
    if (!comms_.connected()) {
        static bool warned = false;
        if (!warned) {
            RCLCPP_WARN(rclcpp::get_logger("NerfSystem"),
                        "Serial disconnected. Skipping write commands.");
            warned = true;
        }
        return hardware_interface::return_type::OK;
    }

    // 0. Manuelles Arming (Position > 0.5 -> ARM, sonst DISARM)
    static bool armed = false;
    bool should_arm = (hw_commands_.arming_pos > 0.5);

    if (should_arm && !armed) {
        comms_.send_command("ARM");  // Aktiviere System
        armed = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: ARM");
    } else if (!should_arm && armed) {
        comms_.send_command("DISARM");  // Deaktiviere System
        armed = false;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: DISARM");
    }

    if (!armed)  // Wenn nicht armed, keine weiteren Commands senden
        return hardware_interface::return_type::OK;

    // 1. Tilt (Trigger Joint) Logik - Verwendet UP/DN Commands für kontinuierliche Rotation
    double target_pos = hw_commands_.trigger_pos;  // Ziel-Position
    double current_pos = hw_states_.trigger_pos;   // Aktuelle Position
    double delta = target_pos - current_pos;       // Differenz

    // Nur bei signifikanter Änderung reagieren (Deadband 0.01 rad)
    if (std::abs(delta) > 0.01) {
        // Berechne Dauer basierend auf Delta-Größe
        // Teleop-Schritt ist 0.05 rad -> ~100ms pro Schritt
        int duration = 100;  // Millisekunden

        // Sende UP oder DN Command an Arduino
        std::stringstream ss;
        if (delta > 0) {
            ss << "UP " << duration;  // Neigung nach oben
            // Update Feedback iterativ anstatt sofort alles zu überschreiben
            hw_states_.trigger_pos += 0.05;
            if (hw_states_.trigger_pos > target_pos) hw_states_.trigger_pos = target_pos;
        } else {
            ss << "DN " << duration;  // Neigung nach unten
            // Update Feedback iterativ anstatt sofort alles zu überschreiben
            hw_states_.trigger_pos -= 0.05;
            if (hw_states_.trigger_pos < target_pos) hw_states_.trigger_pos = target_pos;
        }
        comms_.send_command(ss.str());
    }

    // 2. Pusher (Velocity) - Löst einzelnen Schuss aus bei Velocity > Schwellwert
    static bool pusher_active = false;
    if (hw_commands_.pusher_vel > 1.0 && !pusher_active) {
        // Feuere einen Schuss (Pusher-Zyklus für 500ms)
        comms_.send_command("DANGEROUS_SHOT 500");
        pusher_active = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: DANGEROUS_SHOT");
    } else if (hw_commands_.pusher_vel < 0.1) {
        pusher_active = false;  // Reset bei niedriger Velocity
    }

    // 3. Flywheels (Velocity) - Mappe rad/s auf 0-100% PWM
    double max_vel = 100.0;  // Maximale Geschwindigkeit in rad/s
    // Verwende Durchschnitt beider Räder für einzelnen ESC-Befehl
    double avg_vel =
        (std::abs(hw_commands_.flywheel_l_vel) + std::abs(hw_commands_.flywheel_r_vel)) / 2.0;

    int pwm_percent = static_cast<int>((avg_vel / max_vel) * 100);  // Berechne PWM-Prozent
    pwm_percent = std::max(0, std::min(100, pwm_percent));          // Begrenze auf 0-100%

    static int last_pwm = -1;
    if (pwm_percent == 0 && last_pwm != 0) {
        // Explizit PWM 1000 (Min Throttle) senden zum Stoppen
        // Umgeht Firmware-Bug wo TEST_ESC 0 auf 20% Power setzt
        comms_.send_command("PWM 1000");
        last_pwm = 0;
    } else if (std::abs(pwm_percent - last_pwm) > 2) {
        // Deadband um Traffic zu reduzieren (nur bei Änderung > 2% senden)
        std::stringstream ss;
        ss << "TEST_ESC " << pwm_percent;
        comms_.send_command(ss.str());
        last_pwm = pwm_percent;
    }

    return hardware_interface::return_type::OK;
}

double *NerfSystem::get_state_ptr(const std::string &joint_name,
                                  const std::string &interface_name) {
    // Gebe Zeiger auf State-Variable zurück (für Position oder Velocity)
    if (interface_name == hardware_interface::HW_IF_POSITION) {
        if (joint_name == "trigger_joint") {
            return &hw_states_.trigger_pos;  // Trigger Position
        }
        if (joint_name == "dart_pusher_joint") {
            return &hw_states_.pusher_pos;  // Pusher Position
        }
        if (joint_name == "flywheel_left_joint") {
            return &hw_states_.flywheel_l_pos;  // Linkes Schwungrad Position
        }
        if (joint_name == "flywheel_right_joint") {
            return &hw_states_.flywheel_r_pos;  // Rechtes Schwungrad Position
        }
        if (joint_name == "system_arming_joint") {
            return &hw_states_.arming_pos;  // Arming Position
        }
    }

    if (interface_name == hardware_interface::HW_IF_VELOCITY) {
        if (joint_name == "trigger_joint") {
            return &hw_states_.trigger_vel;  // Trigger Velocity
        }
        if (joint_name == "dart_pusher_joint") {
            return &hw_states_.pusher_vel;  // Pusher Velocity
        }
        if (joint_name == "flywheel_left_joint") {
            return &hw_states_.flywheel_l_vel;  // Linkes Schwungrad Velocity
        }
        if (joint_name == "flywheel_right_joint") {
            return &hw_states_.flywheel_r_vel;  // Rechtes Schwungrad Velocity
        }
        if (joint_name == "system_arming_joint") {
            return &hw_states_.arming_vel;  // Arming Velocity
        }
    }

    return nullptr;  // Interface nicht unterstützt
}

double *NerfSystem::get_command_ptr(const std::string &joint_name,
                                    const std::string &interface_name) {
    // Gebe Zeiger auf Command-Variable zurück (für Position oder Velocity)
    if (joint_name == "trigger_joint" && interface_name == hardware_interface::HW_IF_POSITION) {
        return &hw_commands_.trigger_pos;  // Trigger Position Command
    }

    if (joint_name == "dart_pusher_joint" && interface_name == hardware_interface::HW_IF_VELOCITY) {
        return &hw_commands_.pusher_vel;  // Pusher Velocity Command
    }

    if (joint_name == "flywheel_left_joint" &&
        interface_name == hardware_interface::HW_IF_VELOCITY) {
        return &hw_commands_.flywheel_l_vel;  // Linkes Schwungrad Velocity Command
    }

    if (joint_name == "flywheel_right_joint" &&
        interface_name == hardware_interface::HW_IF_VELOCITY) {
        return &hw_commands_.flywheel_r_vel;  // Rechtes Schwungrad Velocity Command
    }

    if (joint_name == "system_arming_joint" &&
        interface_name == hardware_interface::HW_IF_POSITION) {
        return &hw_commands_.arming_pos;  // Arming Position Command
    }

    return nullptr;  // Interface nicht unterstützt
}

}  // namespace nerf_standalone

// Plugin-Export für ROS2 Control
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(nerf_standalone::NerfSystem, hardware_interface::SystemInterface)
