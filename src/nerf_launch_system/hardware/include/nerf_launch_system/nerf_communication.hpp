/**
 * @file nerf_communication.hpp
 * @brief Serielle Kommunikation mit dem Nerf Launcher Mikrocontroller
 *
 * Verwaltet die LibSerial-Verbindung und sendet Befehle an den Arduino/Pico.
 */
#ifndef NERF_LAUNCH_SYSTEM_NERF_COMMUNICATION_HPP
#define NERF_LAUNCH_SYSTEM_NERF_COMMUNICATION_HPP

#include <cstdint>
#include <libserial/SerialPort.h>
#include <string>

namespace nerf_launch_system {

/**
 * @class NerfCommunication
 * @brief Serielle Kommunikation mit dem Mikrocontroller
 *
 * Kapselt die LibSerial-Verbindung und bietet ein einfaches Interface
 * zum Senden von Befehlen (z.B. "ARM", "SHOT 80", "UP 100").
 */
class NerfCommunication {
public:
    NerfCommunication() = default;

    /**
     * @brief Öffnet serielle Verbindung
     * @param serial_device Device-Pfad (z.B. /dev/ttyACM0)
     * @param baud_rate Baudrate (z.B. 115200)
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
     * @param cmd Befehl-String (z.B. "ARM", "SHOT 80")
     */
    void send_command(const std::string &cmd);

private:
    LibSerial::SerialPort serial_port_;
};

}  // namespace nerf_launch_system

#endif  // NERF_LAUNCH_SYSTEM_NERF_COMMUNICATION_HPP
