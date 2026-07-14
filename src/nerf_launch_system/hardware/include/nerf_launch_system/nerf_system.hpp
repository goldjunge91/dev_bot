/**
 * @file nerf_system.hpp
 * @brief ros2_control Hardware Interface für den Nerf Launcher
 *
 * Implementiert das SystemInterface von ros2_control.
 * Kommuniziert über NerfCommunication mit dem Mikrocontroller.
 *
 * Joints:
 * - tilt_joint: Tilt Servo (Position Control)
 * - shooter_joint: Schuss auslösen (Position = Flywheel Power %)
 * - system_arming_joint: Arming System (Position Control)
 */
#ifndef NERF_LAUNCH_SYSTEM_NERF_SYSTEM_HPP
#define NERF_LAUNCH_SYSTEM_NERF_SYSTEM_HPP

#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "nerf_launch_system/nerf_communication.hpp"
#include "nerf_launch_system/nerf_diagnostics.hpp"
#include "nerf_launch_system/nerf_types.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include <memory>
#include <string>
#include <vector>

namespace nerf_launch_system {

/**
 * @class NerfSystem
 * @brief Haupt Hardware Interface für ros2_control
 *
 * Implementiert SystemInterface und verwaltet alle Nerf Launcher Komponenten.
 * Lifecycle: init -> configure -> activate -> read/write -> deactivate -> cleanup
 */
class NerfSystem : public hardware_interface::SystemInterface {
public:
    using SharedPtr = std::shared_ptr<NerfSystem>;
    using ConstSharedPtr = std::shared_ptr<const NerfSystem>;

    // --- Lifecycle Management ---

    /**
     * @brief Initialisierung: Liest Parameter aus URDF
     * @param info Hardware Info aus URDF (Port, Baudrate, Joints)
     * @return SUCCESS oder ERROR
     */
    hardware_interface::CallbackReturn on_init(
        const hardware_interface::HardwareInfo &info) override;

    /**
     * @brief Konfiguration: Öffnet serielle Verbindung
     * @param previous_state Vorheriger Lifecycle State
     * @return SUCCESS oder ERROR
     */
    hardware_interface::CallbackReturn on_configure(
        const rclcpp_lifecycle::State &previous_state) override;

    /**
     * @brief Cleanup: Schließt serielle Verbindung
     * @param previous_state Vorheriger Lifecycle State
     * @return SUCCESS
     */
    hardware_interface::CallbackReturn on_cleanup(
        const rclcpp_lifecycle::State &previous_state) override;

    /**
     * @brief Aktivierung: System bereit (wartet auf ARM Befehl)
     * @param previous_state Vorheriger Lifecycle State
     * @return SUCCESS
     */
    hardware_interface::CallbackReturn on_activate(
        const rclcpp_lifecycle::State &previous_state) override;

    /**
     * @brief Deaktivierung: Stoppt Motoren und disarmt System
     * @param previous_state Vorheriger Lifecycle State
     * @return SUCCESS
     */
    hardware_interface::CallbackReturn on_deactivate(
        const rclcpp_lifecycle::State &previous_state) override;

    // SystemInterface - Daten-Austausch

    /**
     * @brief Liest Hardware-Zustand (Open-Loop: spiegelt Commands)
     * Hinweis: Wird zwingend für ros2_control benötigt, da Controller stets Feedback erwarten!
     * @param time Aktuelle Zeit
     * @param period Zeit seit letztem read()
     * @return OK
     */
    hardware_interface::return_type read(const rclcpp::Time &time,
                                         const rclcpp::Duration &period) override;

    /**
     * @brief Schreibt Befehle an Hardware (sendet serielle Befehle)
     * @param time Aktuelle Zeit
     * @param period Zeit seit letztem write()
     * @return OK
     */
    hardware_interface::return_type write(const rclcpp::Time &time,
                                          const rclcpp::Duration &period) override;

    /**
     * @brief Exportiert State Interfaces für Controller
     * @return Liste von StateInterface (Position, Velocity)
     */
    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

    /**
     * @brief Exportiert Command Interfaces für Controller
     * @return Liste von CommandInterface (Position, Velocity)
     */
    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

private:
    NerfCommunication comms_;    // Serielle Kommunikation
    NerfJoints hw_commands_;     // Befehle von Controllern
    NerfJointStates hw_states_;  // Zustand für Controller (Open-Loop Feedback)

    // /diagnostics-Reporting (Serial-Verbindung, Armed-Status, Loop-Rate).
    // Angelegt in on_configure(), gestartet/gestoppt entlang des Serial-
    // Verbindungs-Lifecycles. Siehe nerf_diagnostics.hpp — gleiches Muster
    // wie mecanum_pico::HardwareDiagnostics (eigener Node/Thread, da
    // SystemInterface keinen eigenen rclcpp::Node besitzt).
    std::unique_ptr<NerfDiagnostics> diagnostics_;

    // Konfiguration aus URDF
    std::string port_;  // Serieller Port (z.B. /dev/ttyACM0)
    int baud_rate_;     // Baudrate (z.B. 115200)

    // Referenz-Rate für die Loop-Rate-Diagnose (optional, Default: 100 Hz —
    // das controller_manager update_rate laut config/controllers.yaml).
    // Dieses Hardware-Interface kennt seine eigene Aufruf-Rate nicht, daher
    // ist dies nur ein konfigurierbarer Vergleichswert für die Diagnose.
    double diagnostics_expected_rate_hz_ = 100.0;

    // Tilt-Range in Joint-Space (rad) — das Hardware-Interface besitzt die
    // Konvention: alle Nodes kommandieren im URDF-Joint-Bereich, write()
    // clampt darauf. Die Firmware selbst ist einheitenlos (relative UP/DN-
    // Pulse), daher genügt der Clamp hier.
    // ALT: Nodes kommandierten Servo-Rohwerte 5.23–6.28 rad — kollidierte
    //      mit den URDF-Limits (±0.52) in der Simulation.
    double tilt_min_ = -0.52;  // URDF trigger_joint lower limit (rad)
    double tilt_max_ = 0.52;   // URDF trigger_joint upper limit (rad)

    // Arming State (Synchron mit Firmware-FSM)
    /**
     * @brief Gibt Pointer auf State-Variable zurück
     * @param joint_name Name des Joints
     * @param interface_name Interface-Typ (position/velocity)
     * @return Pointer auf double oder nullptr
     */
    bool armed_ = false;
    bool pusher_active_ = false;
    bool serial_warned_ = false;

    double *get_state_ptr(const std::string &joint_name, const std::string &interface_name);

    /**
     * @brief Gibt Pointer auf Command-Variable zurück
     * @param joint_name Name des Joints
     * @param interface_name Interface-Typ (position/velocity)
     * @return Pointer auf double oder nullptr
     */
    double *get_command_ptr(const std::string &joint_name, const std::string &interface_name);
};

}  // namespace nerf_launch_system

#endif  // NERF_LAUNCH_SYSTEM_NERF_SYSTEM_HPP
