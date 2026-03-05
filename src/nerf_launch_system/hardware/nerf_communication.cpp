/**
 * @file nerf_communication.cpp
 * @brief Implementierung der seriellen Kommunikation mit dem Mikrocontroller
 */
#include "nerf_launch_system/nerf_communication.hpp"

#include "rclcpp/logging.hpp"

namespace nerf_launch_system {

void NerfCommunication::connect(const std::string &serial_device, int32_t baud_rate) {
    LibSerial::BaudRate baud;
    switch (baud_rate) {
        case 9600:
            baud = LibSerial::BaudRate::BAUD_9600;
            break;
        case 57600:
            baud = LibSerial::BaudRate::BAUD_57600;
            break;
        case 115200:
            baud = LibSerial::BaudRate::BAUD_115200;
            break;
        default:
            baud = LibSerial::BaudRate::BAUD_115200;
            break;
    }

    serial_port_.Open(serial_device);
    serial_port_.SetBaudRate(baud);
    serial_port_.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serial_port_.SetFlowControl(LibSerial::FlowControl::FLOW_CONTROL_NONE);
    serial_port_.SetParity(LibSerial::Parity::PARITY_NONE);
    serial_port_.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
}

void NerfCommunication::disconnect() {
    if (serial_port_.IsOpen()) {
        try {
            serial_port_.Close();
        } catch (const std::exception &e) {
            RCLCPP_ERROR(
                rclcpp::get_logger("NerfCommunication"), "Error closing serial port: %s", e.what());
        }
    }
}

bool NerfCommunication::connected() const {
    return serial_port_.IsOpen();
}

void NerfCommunication::send_command(const std::string &cmd) {
    if (!serial_port_.IsOpen()) return;

    try {
        serial_port_.Write(cmd + "\n");
    } catch (const std::exception &e) {
        RCLCPP_ERROR(rclcpp::get_logger("NerfCommunication"),
                     "Serial write failed (%s). Closing port.",
                     e.what());
        disconnect();
    }
}

}  // namespace nerf_launch_system
