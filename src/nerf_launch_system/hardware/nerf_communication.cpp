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
            RCLCPP_ERROR(rclcpp::get_logger("NerfCommunication"),
                         "{'id': 'serial_error', 'error': '%s'} Error closing serial port",
                         e.what());
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
                     "{'id': 'serial_error', 'error': '%s'} Serial write failed. Closing port.",
                     e.what());
        disconnect();
    }
}

}  // namespace nerf_launch_system
