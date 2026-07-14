/**
 * @file nerf_system.cpp
 * @brief Implementierung des ros2_control Hardware Interface für den Nerf Launcher
 */
#include "nerf_launch_system/nerf_system.hpp"

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/logging.hpp"

#include <algorithm>
#include <cmath>
#include <rclcpp_lifecycle/state.hpp>
#include <sstream>
#include <vector>

namespace nerf_launch_system {

// --- Lifecycle ---

hardware_interface::CallbackReturn NerfSystem::on_init(
    const hardware_interface::HardwareInfo &info) {
    if (hardware_interface::SystemInterface::on_init(info) !=
        hardware_interface::CallbackReturn::SUCCESS) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    port_ = info_.hardware_parameters["port"];
    baud_rate_ = std::stoi(info_.hardware_parameters["baud_rate"]);

    // Tilt-Range aus URDF (optional, Default: ±0.52 rad = trigger_joint Limits)
    if (info_.hardware_parameters.count("tilt_min")) {
        tilt_min_ = std::stod(info_.hardware_parameters.at("tilt_min"));
    }
    if (info_.hardware_parameters.count("tilt_max")) {
        tilt_max_ = std::stod(info_.hardware_parameters.at("tilt_max"));
    }
    if (info_.hardware_parameters.count("diagnostics_expected_rate_hz")) {
        diagnostics_expected_rate_hz_ =
            std::stod(info_.hardware_parameters.at("diagnostics_expected_rate_hz"));
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

        // Erlaubte Joints laut URDF (gubot_one/ros2_control_hardware.xacro):
        // trigger_joint (Tilt), dart_pusher_joint (Shooter), system_arming_joint (Arming)
        // ALT: tilt_joint und shooter_joint waren Legacy-Aliase vor URDF-Umbenennung
        if (joint.name != "trigger_joint" &&
            // joint.name != "tilt_joint" &&    // ALT: Legacy-Alias, URDF nutzt trigger_joint
            // joint.name != "shooter_joint" && // ALT: Legacy-Alias, URDF nutzt dart_pusher_joint
            joint.name != "dart_pusher_joint" && joint.name != "system_arming_joint") {
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
                                                 const rclcpp::Duration & /*period*/) {
    if (diagnostics_) {
        diagnostics_->note_read_cycle();
    }

    // Open-Loop: Spiegle Commands in States
    auto safe_copy = [](double src, double &dst) {
        if (std::isfinite(src)) {
            dst = src;
        }
    };

    safe_copy(hw_commands_.tilt_pos, hw_states_.tilt_pos);
    safe_copy(hw_commands_.shooter_pos, hw_states_.shooter_pos);
    safe_copy(hw_commands_.arming_pos, hw_states_.arming_pos);

    // Sicherheitsprüfung: keine NaN/Inf in States
    auto sanitize = [](double &v) {
        if (!std::isfinite(v)) v = 0.0;
    };
    sanitize(hw_states_.tilt_pos);
    sanitize(hw_states_.shooter_pos);
    sanitize(hw_states_.arming_pos);

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

    // 1. Tilt – UP/DN Commands für kontinuierliche Rotation
    // Clamp auf die Joint-Range: das Hardware-Interface besitzt die Konvention.
    // Out-of-Range-Kommandos (z. B. alte Servo-Rohwerte 5.23–6.28) laufen so
    // nicht mehr endlos gegen die mechanische Grenze.
    double target_pos = std::clamp(hw_commands_.tilt_pos, tilt_min_, tilt_max_);
    double current_pos = hw_states_.tilt_pos;
    double delta = target_pos - current_pos;

    if (std::abs(delta) > 0.01) {
        int duration = 100;  // Millisekunden

        std::stringstream ss;
        if (delta > 0) {
            ss << "UP " << duration;
            hw_states_.tilt_pos += 0.05;
            if (hw_states_.tilt_pos > target_pos) hw_states_.tilt_pos = target_pos;
        } else {
            ss << "DN " << duration;
            hw_states_.tilt_pos -= 0.05;
            if (hw_states_.tilt_pos < target_pos) hw_states_.tilt_pos = target_pos;
        }
        send_and_check(ss.str());
    }

    // 2. Schuss – SHOT delegiert die komplette Sequenz an die FiringFSM
    //    (SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED)
    // shooter_pos = Flywheel Power % (0-100), Wert > 0 löst einmalig SHOT aus
    int shot_power = static_cast<int>(hw_commands_.shooter_pos);
    if (shot_power > 0 && !pusher_active_) {
        std::stringstream shot_ss;
        shot_ss << "SHOT " << shot_power;
        send_and_check(shot_ss.str());
        pusher_active_ = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"), "Command: SHOT %d (via FSM)", shot_power);
    } else if (shot_power <= 0) {
        pusher_active_ = false;
    }

    // Hinweis: Flywheels und Pusher-Sequence werden von der Firmware-FSM autonom gesteuert.
    // Ein SHOT-Befehl löst die komplette interne Sequenz aus.
    return hardware_interface::return_type::OK;
}

// --- Pointer Lookup ---

double *NerfSystem::get_state_ptr(const std::string &joint_name,
                                  const std::string &interface_name) {
    if (interface_name == hardware_interface::HW_IF_POSITION) {
        // trigger_joint ist der aktuelle URDF-Name (gubot_one/ros2_control_hardware.xacro)
        // ALT: tilt_joint war der Legacy-Name vor der URDF-Umbenennung
        if (joint_name == "trigger_joint" /* || joint_name == "tilt_joint" */) {
            return &hw_states_.tilt_pos;
        }
        if (joint_name == "system_arming_joint") {
            return &hw_states_.arming_pos;
        }
    }
    // dart_pusher_joint hat velocity command_interface in der URDF
    if (interface_name == hardware_interface::HW_IF_VELOCITY) {
        // dart_pusher_joint ist der aktuelle URDF-Name (velocity interface)
        // ALT: shooter_joint war der Legacy-Name
        if (joint_name == "dart_pusher_joint" /* || joint_name == "shooter_joint" */) {
            return &hw_states_.shooter_pos;
        }
    }

    return nullptr;
}

double *NerfSystem::get_command_ptr(const std::string &joint_name,
                                    const std::string &interface_name) {
    // trigger_joint ist der aktuelle URDF-Name (gubot_one/ros2_control_hardware.xacro)
    // ALT: tilt_joint war der Legacy-Name vor der URDF-Umbenennung
    if ((joint_name == "trigger_joint" /* || joint_name == "tilt_joint" */) &&
        interface_name == hardware_interface::HW_IF_POSITION) {
        return &hw_commands_.tilt_pos;
    }

    // dart_pusher_joint hat velocity command_interface laut URDF (ros2_control_hardware.xacro)
    // ALT: shooter_joint war der Legacy-Name
    if ((joint_name == "dart_pusher_joint" /* || joint_name == "shooter_joint" */) &&
        interface_name == hardware_interface::HW_IF_VELOCITY) {
        return &hw_commands_.shooter_pos;
    }

    if (joint_name == "system_arming_joint" &&
        interface_name == hardware_interface::HW_IF_POSITION) {
        return &hw_commands_.arming_pos;
    }

    return nullptr;
}

}  // namespace nerf_launch_system

// Plugin-Export für ROS2 Control
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(nerf_launch_system::NerfSystem, hardware_interface::SystemInterface)
