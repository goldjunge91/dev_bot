/**
 * @file nerf_system.cpp
 * @brief Implementierung des ros2_control Hardware Interface für den Nerf Launcher
 */
#include "nerf_launch_system/nerf_system.hpp"

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "nerf_launch_system/nerf_command_logic.hpp"
#include "rclcpp/logging.hpp"

#include <cmath>
#include <rclcpp_lifecycle/state.hpp>
#include <vector>

namespace nerf_launch_system {

namespace {

// Einzige Quelle der Wahrheit für Joint <-> Interface <-> Speicher-Mapping.
// Ersetzt die vorherigen if-Kaskaden in get_state_ptr()/get_command_ptr()
// und die manuelle Joint-Namensliste in on_init(): alle drei leiten sich
// aus dieser einen Tabelle ab.
struct InterfaceEntry {
    const char *joint_name;
    const char *interface_name;
    double NerfJoints::*command_member;       // nullptr, falls kein Command-Interface
    double NerfJointStates::*state_member;    // nullptr, falls kein State-Interface
};

const InterfaceEntry kInterfaceTable[] = {
    {"trigger_joint",
     hardware_interface::HW_IF_POSITION,
     &NerfJoints::tilt_pos,
     &NerfJointStates::tilt_pos},
    {"dart_pusher_joint",
     hardware_interface::HW_IF_VELOCITY,
     &NerfJoints::shooter_pos,
     &NerfJointStates::shooter_pos},
    // Kein Command-Member: reine State-Interface, in read() aus shooter_pos
    // integriert (siehe NerfJointStates::dart_pusher_pos).
    {"dart_pusher_joint",
     hardware_interface::HW_IF_POSITION,
     nullptr,
     &NerfJointStates::dart_pusher_pos},
    {"system_arming_joint",
     hardware_interface::HW_IF_POSITION,
     &NerfJoints::arming_pos,
     &NerfJointStates::arming_pos},
};

bool is_known_joint(const std::string &joint_name) {
    for (const auto &entry : kInterfaceTable) {
        if (joint_name == entry.joint_name) {
            return true;
        }
    }
    return false;
}

}  // namespace

// --- Lifecycle ---

hardware_interface::CallbackReturn NerfSystem::on_init(
    const hardware_interface::HardwareInfo &info) {
    if (hardware_interface::SystemInterface::on_init(info) !=
        hardware_interface::CallbackReturn::SUCCESS) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    if (!info_.hardware_parameters.count("port")) {
        RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                     "Missing required hardware parameter 'port'");
        return hardware_interface::CallbackReturn::ERROR;
    }
    port_ = info_.hardware_parameters.at("port");

    if (!info_.hardware_parameters.count("baud_rate")) {
        RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                     "Missing required hardware parameter 'baud_rate'");
        return hardware_interface::CallbackReturn::ERROR;
    }
    try {
        baud_rate_ = std::stoi(info_.hardware_parameters.at("baud_rate"));
    } catch (const std::exception &e) {
        RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                     "Invalid 'baud_rate' hardware parameter ('%s'): %s",
                     info_.hardware_parameters.at("baud_rate").c_str(),
                     e.what());
        return hardware_interface::CallbackReturn::ERROR;
    }

    // Optionale numerische Parameter: Key vorhanden, aber Wert nicht
    // parsebar -> ERROR statt uncaught std::invalid_argument.
    auto parse_optional_double = [this](const std::string &key, double &target) -> bool {
        if (!info_.hardware_parameters.count(key)) {
            return true;
        }
        try {
            target = std::stod(info_.hardware_parameters.at(key));
        } catch (const std::exception &e) {
            RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                         "Invalid '%s' hardware parameter ('%s'): %s",
                         key.c_str(),
                         info_.hardware_parameters.at(key).c_str(),
                         e.what());
            return false;
        }
        return true;
    };

    // Tilt-Range aus URDF (optional, Default: ±0.52 rad = trigger_joint Limits)
    if (!parse_optional_double("tilt_min", tilt_min_) ||
        !parse_optional_double("tilt_max", tilt_max_) ||
        !parse_optional_double("diagnostics_expected_rate_hz", diagnostics_expected_rate_hz_)) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "Initialized NerfSystem on port %s @ %d (tilt range [%.2f, %.2f] rad)",
                port_.c_str(),
                baud_rate_,
                tilt_min_,
                tilt_max_);

    // Verifiziere Joints aus URDF-Konfiguration
    for (const hardware_interface::ComponentInfo &joint : info_.joints) {
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Joint found: %s", joint.name.c_str());

        if (!is_known_joint(joint.name)) {
            RCLCPP_FATAL(
                rclcpp::get_logger("NerfSystem"), "Unsupported joint '%s'", joint.name.c_str());
            return hardware_interface::CallbackReturn::ERROR;
        }

        for (const auto &command_interface : joint.command_interfaces) {
            if (!get_command_ptr(joint.name, command_interface.name)) {
                RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                             "Unsupported command interface '%s' for joint '%s'",
                             command_interface.name.c_str(),
                             joint.name.c_str());
                return hardware_interface::CallbackReturn::ERROR;
            }
        }

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

hardware_interface::CallbackReturn NerfSystem::on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(
        rclcpp::get_logger("NerfSystem"), "Configuring... Opening Serial %s", port_.c_str());
    try {
        comms_.connect(port_, baud_rate_);
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Serial Connected Successfully");
    } catch (const std::exception &e) {
        RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"), "Failed to open serial port: %s", e.what());
        return hardware_interface::CallbackReturn::ERROR;
    }

    // Health reporting (/diagnostics) for the serial link + control-loop
    // rate. Created fresh on every on_configure() so a previous run's
    // failure counters don't leak across reconfigurations.
    diagnostics_ = std::make_unique<NerfDiagnostics>(
        get_name(), port_, baud_rate_, diagnostics_expected_rate_hz_);
    diagnostics_->set_connected(comms_.connected());
    diagnostics_->start();

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_cleanup(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    comms_.disconnect();
    if (diagnostics_) {
        diagnostics_->stop();
        diagnostics_.reset();
    }
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System Activated (Waiting for ARM command)");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    comms_.send_command("DISARM");
    armed_ = false;
    if (diagnostics_) {
        diagnostics_->set_armed(false);
        diagnostics_->set_connected(comms_.connected());
    }
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "System DISARMED");
    return hardware_interface::CallbackReturn::SUCCESS;
}

// --- Interface Export ---

std::vector<hardware_interface::StateInterface> NerfSystem::export_state_interfaces() {
    std::vector<hardware_interface::StateInterface> state_interfaces;

    for (const auto &joint : info_.joints) {
        for (const auto &interface : joint.state_interfaces) {
            double *state_ptr = get_state_ptr(joint.name, interface.name);
            if (!state_ptr) {
                RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                             "Skipping unsupported state interface '%s' for joint '%s'",
                             interface.name.c_str(),
                             joint.name.c_str());
                continue;
            }
            state_interfaces.emplace_back(
                hardware_interface::StateInterface(joint.name, interface.name, state_ptr));
        }
    }

    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> NerfSystem::export_command_interfaces() {
    std::vector<hardware_interface::CommandInterface> command_interfaces;

    for (const auto &joint : info_.joints) {
        for (const auto &interface : joint.command_interfaces) {
            double *command_ptr = get_command_ptr(joint.name, interface.name);
            if (!command_ptr) {
                RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                             "Skipping unsupported command interface '%s' for joint '%s'",
                             interface.name.c_str(),
                             joint.name.c_str());
                continue;
            }
            command_interfaces.emplace_back(
                hardware_interface::CommandInterface(joint.name, interface.name, command_ptr));
        }
    }

    return command_interfaces;
}

// --- Read / Write ---

hardware_interface::return_type NerfSystem::read(const rclcpp::Time & /*time*/,
                                                 const rclcpp::Duration &period) {
    if (diagnostics_) {
        diagnostics_->note_read_cycle();
    }

    // Open-Loop: Spiegle Commands in States.
    // tilt_pos ist davon ausgenommen: write() integriert dort inkrementell
    // (UP/DN-Pulse) auf den tatsächlichen Servo-Fortschritt. Würde read()
    // den Command hineinspiegeln, wäre delta = target - state in write()
    // sofort ~0 und es würde nie ein UP/DN-Kommando gesendet.
    auto safe_copy = [](double src, double &dst) {
        if (std::isfinite(src)) {
            dst = src;
        }
    };

    safe_copy(hw_commands_.shooter_pos, hw_states_.shooter_pos);
    safe_copy(hw_commands_.arming_pos, hw_states_.arming_pos);

    // dart_pusher_joint hat keinen echten Encoder — Position wird aus dem
    // Geschwindigkeits-Kommando integriert (Standard-Konvention fuer
    // "position += velocity * dt" bei continuous Joints), nur damit
    // joint_state_broadcaster kein NaN mehr fuer dieses Joint meldet (siehe
    // NerfJointStates::dart_pusher_pos). Physikalisch nicht kalibriert, rein
    // fuer eine gueltige, sich bewegende TF/RViz-Darstellung waehrend eines
    // Schusses; laeuft frei (kein Wraparound noetig, continuous Joint).
    if (std::isfinite(hw_commands_.shooter_pos)) {
        constexpr double kPusherRadPerSecAtFullPower = 2.0 * M_PI;  // willkuerlich: 1 U/s bei 100%
        hw_states_.dart_pusher_pos +=
            (hw_commands_.shooter_pos / 100.0) * kPusherRadPerSecAtFullPower * period.seconds();
    }

    // Sicherheitsprüfung: keine NaN/Inf in States
    auto sanitize = [](double &v) {
        if (!std::isfinite(v)) v = 0.0;
    };
    sanitize(hw_states_.tilt_pos);
    sanitize(hw_states_.shooter_pos);
    sanitize(hw_states_.arming_pos);
    sanitize(hw_states_.dart_pusher_pos);

    return hardware_interface::return_type::OK;
}

hardware_interface::return_type NerfSystem::write(const rclcpp::Time & /*time*/,
                                                  const rclcpp::Duration & /*period*/) {
    // Wraps comms_.send_command() and reports a write failure to
    // diagnostics_ if the serial link drops as a result (NerfCommunication
    // disconnects internally when a write throws — no return value to
    // check, so we detect it via the connected() state transition).
    auto send_and_check = [this](const std::string &cmd) {
        comms_.send_command(cmd);
        if (diagnostics_ && !comms_.connected()) {
            diagnostics_->note_write_failure();
        }
    };

    if (diagnostics_) {
        diagnostics_->set_connected(comms_.connected());
    }
    if (!comms_.connected()) {
        if (!serial_warned_) {
            RCLCPP_WARN(rclcpp::get_logger("NerfSystem"),
                        "Serial disconnected. Skipping write commands.");
            serial_warned_ = true;
        }
        return hardware_interface::return_type::OK;
    }
    serial_warned_ = false;

    // 0. Arming (Position > 0.5 -> ARM, sonst DISARM)
    bool should_arm = (hw_commands_.arming_pos > 0.5);

    if (should_arm && !armed_) {
        send_and_check("ARM");
        armed_ = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: ARM");
    } else if (!should_arm && armed_) {
        send_and_check("DISARM");
        armed_ = false;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: DISARM");
    }
    if (diagnostics_) {
        diagnostics_->set_armed(armed_);
    }

    if (!armed_) return hardware_interface::return_type::OK;

    // 1. Tilt – UP/DN Commands für kontinuierliche Rotation.
    // Clamp auf die Joint-Range passiert in make_tilt_command(): das
    // Hardware-Interface besitzt die Konvention. Out-of-Range-Kommandos
    // (z. B. alte Servo-Rohwerte 5.23–6.28) laufen so nicht mehr endlos
    // gegen die mechanische Grenze.
    auto tilt_step = make_tilt_command(hw_commands_.tilt_pos, hw_states_.tilt_pos,
                                       tilt_min_, tilt_max_);
    if (tilt_step) {
        hw_states_.tilt_pos = tilt_step->new_tilt_pos;
        send_and_check(tilt_step->command);
    }

    // 2. Schuss – SHOT delegiert die komplette Sequenz an die FiringFSM
    //    (SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED)
    // shooter_pos = Flywheel Power % (0-100), Wert > 0 löst einmalig SHOT aus
    auto shot_cmd = make_shot_command(hw_commands_.shooter_pos, pusher_active_);
    if (shot_cmd) {
        send_and_check(*shot_cmd);
        RCLCPP_INFO(
            rclcpp::get_logger("NerfSystem"), "Command: %s (via FSM)", shot_cmd->c_str());
    }

    // Hinweis: Flywheels und Pusher-Sequence werden von der Firmware-FSM autonom gesteuert.
    // Ein SHOT-Befehl löst die komplette interne Sequenz aus.
    return hardware_interface::return_type::OK;
}

// --- Pointer Lookup ---

double *NerfSystem::get_state_ptr(const std::string &joint_name,
                                  const std::string &interface_name) {
    for (const auto &entry : kInterfaceTable) {
        if (joint_name == entry.joint_name && interface_name == entry.interface_name &&
            entry.state_member) {
            return &(hw_states_.*entry.state_member);
        }
    }
    return nullptr;
}

double *NerfSystem::get_command_ptr(const std::string &joint_name,
                                    const std::string &interface_name) {
    for (const auto &entry : kInterfaceTable) {
        if (joint_name == entry.joint_name && interface_name == entry.interface_name &&
            entry.command_member) {
            return &(hw_commands_.*entry.command_member);
        }
    }
    return nullptr;
}

}  // namespace nerf_launch_system

// Plugin-Export für ROS2 Control
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(nerf_launch_system::NerfSystem, hardware_interface::SystemInterface)
