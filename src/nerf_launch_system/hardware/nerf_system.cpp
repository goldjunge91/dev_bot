// Copyright 2026 Developer
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @file nerf_system.cpp
 * @brief Implementierung des ros2_control Hardware Interface für den Nerf Launcher
 */
#include "nerf_launch_system/nerf_system.hpp"

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/logging.hpp"

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

    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "{'id': 'init', 'port': '%s', 'baud': %d} Initialized NerfSystem",
                port_.c_str(),
                baud_rate_);

    // Verifiziere Joints aus URDF-Konfiguration
    for (const hardware_interface::ComponentInfo &joint : info_.joints) {
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                    "{'id': 'joint_discovery', 'name': '%s'} Joint found",
                    joint.name.c_str());

        if (joint.name != "tilt_joint" &&
            joint.name != "trigger_joint" &&  // Fallback falls URDF noch nicht aktualisiert
            joint.name != "shooter_joint" && joint.name != "system_arming_joint") {
            RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                         "{'id': 'unsupported_joint', 'name': '%s'} Unsupported joint",
                         joint.name.c_str());
            return hardware_interface::CallbackReturn::ERROR;
        }

        for (const auto &command_interface : joint.command_interfaces) {
            if (!get_command_ptr(joint.name, command_interface.name)) {
                RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                             "{'id': 'unsupported_interface', 'joint': '%s', 'type': '%s'} "
                             "Unsupported command interface",
                             joint.name.c_str(),
                             command_interface.name.c_str());
                return hardware_interface::CallbackReturn::ERROR;
            }
        }

        for (const auto &state_interface : joint.state_interfaces) {
            if (!get_state_ptr(joint.name, state_interface.name)) {
                RCLCPP_FATAL(rclcpp::get_logger("NerfSystem"),
                             "{'id': 'unsupported_interface', 'joint': '%s', 'type': '%s'} "
                             "Unsupported state interface",
                             joint.name.c_str(),
                             state_interface.name.c_str());
                return hardware_interface::CallbackReturn::ERROR;
            }
        }
    }

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "{'id': 'configure', 'port': '%s'} Configuring... Opening Serial",
                port_.c_str());
    try {
        comms_.connect(port_, baud_rate_);
        RCLCPP_INFO(
            rclcpp::get_logger("NerfSystem"),
            "{'id': 'serial_status', 'attribute': 'connected'} Serial Connected Successfully");
    } catch (const std::exception &e) {
        RCLCPP_ERROR(rclcpp::get_logger("NerfSystem"),
                     "{'id': 'serial_error', 'error': '%s'} Failed to open serial port",
                     e.what());
        return hardware_interface::CallbackReturn::ERROR;
    }
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_cleanup(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    comms_.disconnect();
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(
        rclcpp::get_logger("NerfSystem"),
        "{'id': 'status', 'state': 'activated'} System Activated (Waiting for ARM command)");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn NerfSystem::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
    comms_.send_command("DISARM");
    armed_ = false;
    RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                "{'id': 'status', 'state': 'disarmed'} System DISARMED");
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
                             "{'id': 'unsupported_export', 'joint': '%s', 'type': '%s'} Skipping "
                             "unsupported state interface",
                             joint.name.c_str(),
                             interface.name.c_str());
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
                             "{'id': 'unsupported_export', 'joint': '%s', 'type': '%s'} Skipping "
                             "unsupported command interface",
                             joint.name.c_str(),
                             interface.name.c_str());
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
    if (!comms_.connected()) {
        if (!serial_warned_) {
            RCLCPP_WARN(rclcpp::get_logger("NerfSystem"),
                        "{'id': 'serial_status', 'attribute': 'disconnected'} Serial disconnected. "
                        "Skipping write commands.");
            serial_warned_ = true;
        }
        return hardware_interface::return_type::OK;
    }
    serial_warned_ = false;

    // 0. Arming (Position > 0.5 -> ARM, sonst DISARM)
    bool should_arm = (hw_commands_.arming_pos > 0.5);

    if (should_arm && !armed_) {
        comms_.send_command("ARM");
        armed_ = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                    "{'id': 'command', 'action': 'ARM'} Command sent");
    } else if (!should_arm && armed_) {
        comms_.send_command("DISARM");
        armed_ = false;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                    "{'id': 'command', 'action': 'DISARM'} Command sent");
    }

    if (!armed_) return hardware_interface::return_type::OK;

    // 1. Tilt – UP/DN Commands für kontinuierliche Rotation
    double target_pos = hw_commands_.tilt_pos;
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
        comms_.send_command(ss.str());
    }

    // 2. Schuss – SHOT delegiert die komplette Sequenz an die FiringFSM
    //    (SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED)
    // shooter_pos = Flywheel Power % (0-100), Wert > 0 löst einmalig SHOT aus
    int shot_power = static_cast<int>(hw_commands_.shooter_pos);
    if (shot_power > 0 && !pusher_active_) {
        std::stringstream shot_ss;
        shot_ss << "SHOT " << shot_power;
        comms_.send_command(shot_ss.str());
        pusher_active_ = true;
        RCLCPP_INFO(rclcpp::get_logger("NerfSystem"),
                    "{'id': 'command', 'action': 'SHOT', 'power': %d} Command sent (via FSM)",
                    shot_power);
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
        if (joint_name == "trigger_joint" || joint_name == "tilt_joint") {
            return &hw_states_.tilt_pos;
        }
        if (joint_name == "shooter_joint") {
            return &hw_states_.shooter_pos;
        }
        if (joint_name == "system_arming_joint") {
            return &hw_states_.arming_pos;
        }
    }

    return nullptr;
}

double *NerfSystem::get_command_ptr(const std::string &joint_name,
                                    const std::string &interface_name) {
    if ((joint_name == "trigger_joint" || joint_name == "tilt_joint") &&
        interface_name == hardware_interface::HW_IF_POSITION) {
        return &hw_commands_.tilt_pos;
    }

    if (joint_name == "shooter_joint" && interface_name == hardware_interface::HW_IF_POSITION) {
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
