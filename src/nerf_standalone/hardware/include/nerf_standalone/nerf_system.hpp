/**
 * @file nerf_system.hpp
 * @brief Hardware Interface für Nerf Launcher mit ros2_control
 *
 * Dieses File definiert das Hardware Interface für den Nerf Launcher.
 * Es implementiert das SystemInterface von ros2_control und kommuniziert
 * über serielle Verbindung mit dem Arduino/Mikrocontroller.
 *
 * Komponenten:
 * - NerfJoints: Befehle an Hardware (Commands)
 * - NerfJointStates: Zustand der Hardware (States/Feedback)
 * - NerfComms: Serielle Kommunikation
 * - NerfSystem: Hauptklasse (ros2_control SystemInterface)
 *
 * Joints:
 * - trigger_joint: Tilt Servo (Position Control)
 * - dart_pusher_joint: Pusher Servo (Velocity Control)
 * - flywheel_left_joint: Linker Flywheel Motor (Velocity Control)
 * - flywheel_right_joint: Rechter Flywheel Motor (Velocity Control)
 * - system_arming_joint: Arming System (Position Control)
 */
#ifndef NERF_STANDALONE_NERF_SYSTEM_HPP
#define NERF_STANDALONE_NERF_SYSTEM_HPP

#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include <libserial/SerialPort.h>
#include <memory>
#include <string>
#include <vector>

namespace nerf_standalone {

/**
 * @struct NerfJoints
 * @brief Befehle an die Hardware (Command Interface)
 *
 * Diese Werte werden von Controllern gesetzt und in write() an Hardware gesendet
 */
struct NerfJoints {
    double trigger_pos = 0.0;     // Tilt Servo Position in Radiant (5.23-6.28 rad)
    double pusher_vel = 0.0;      // Pusher Geschwindigkeit (>1.0 = Schuss auslösen)
    double flywheel_l_vel = 0.0;  // Linker Flywheel Geschwindigkeit in rad/s
    double flywheel_r_vel = 0.0;  // Rechter Flywheel Geschwindigkeit in rad/s
    double arming_pos = 0.0;      // Arming Status (>0.5 = Armed, <0.5 = Disarmed)
};

/**
 * @struct NerfJointStates
 * @brief Zustand der Hardware (State Interface)
 *
 * Diese Werte werden in read() aktualisiert und von Controllern gelesen
 * Open-Loop: Wir spiegeln Commands in States (keine echten Encoder)
 */
struct NerfJointStates {
    double trigger_pos = 0.0;     // Aktuelle Tilt Position
    double trigger_vel = 0.0;     // Tilt Geschwindigkeit (immer 0, kein Feedback)
    double pusher_pos = 0.0;      // Pusher Position (nicht verwendet)
    double pusher_vel = 0.0;      // Pusher Geschwindigkeit
    double flywheel_l_pos = 0.0;  // Linker Flywheel Position (nicht verwendet)
    double flywheel_l_vel = 0.0;  // Linker Flywheel Geschwindigkeit
    double flywheel_r_pos = 0.0;  // Rechter Flywheel Position (nicht verwendet)
    double flywheel_r_vel = 0.0;  // Rechter Flywheel Geschwindigkeit
    double arming_pos = 0.0;      // Arming Status
    double arming_vel = 0.0;      // Arming Geschwindigkeit (nicht verwendet)
};

/**
 * @class NerfComms
 * @brief Serielle Kommunikation mit Mikrocontroller
 *
 * Verwaltet die serielle Verbindung und sendet Befehle an Arduino/Pico
 */
class NerfComms {
public:
    NerfComms() = default;

    /**
     * @brief Öffnet serielle Verbindung
     * @param serial_device Device-Pfad (z.B. /dev/ttyACM0)
     * @param baud_rate Baudrate (z.B. 57600)
     */
    void connect(const std::string &serial_device, int32_t baud_rate);

    /**
     * @brief Schließt serielle Verbindung
     */
    void disconnect();

    /**
     * @brief Prüft ob Verbindung aktiv ist
     * @return true wenn verbunden
     */
    bool connected() const;

    /**
     * @brief Sendet Befehl an Mikrocontroller
     * @param cmd Befehl-String (z.B. "ARM", "TEST_ESC 50")
     */
    void send_command(const std::string &cmd);

private:
    LibSerial::SerialPort serial_conn_;  // LibSerial Verbindung
};

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

    // LifecycleNodeInterface - Lifecycle Management

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
    NerfComms comms_;            // Serielle Kommunikation
    NerfJoints hw_commands_;     // Befehle von Controllern
    NerfJointStates hw_states_;  // Zustand für Controller (Open-Loop Feedback)

    // Konfiguration aus URDF
    std::string port_;  // Serieller Port (z.B. /dev/ttyACM0)
    int baud_rate_;     // Baudrate (z.B. 57600)

    // Arming State (Synchron mit Firmware-FSM)
    bool armed_ = false;          // Ob das System gearmt ist
    bool pusher_active_ = false;  // Ob ein Schuss aktiv ist (verhindert Doppel-SHOT)

    // Tilt Servo Grenzen in Radiant
    double tilt_min_rad_ = 5.23;  // ~300° (Unten)
    double tilt_max_rad_ = 6.28;  // ~360° (Oben)

    /**
     * @brief Gibt Pointer auf State-Variable zurück
     * @param joint_name Name des Joints
     * @param interface_name Interface-Typ (position/velocity)
     * @return Pointer auf double oder nullptr
     */
    double *get_state_ptr(const std::string &joint_name, const std::string &interface_name);

    /**
     * @brief Gibt Pointer auf Command-Variable zurück
     * @param joint_name Name des Joints
     * @param interface_name Interface-Typ (position/velocity)
     * @return Pointer auf double oder nullptr
     */
    double *get_command_ptr(const std::string &joint_name, const std::string &interface_name);
};

}  // namespace nerf_standalone

#endif  // NERF_STANDALONE_NERF_SYSTEM_HPP
