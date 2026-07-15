// MIGRATION STATUS: COMPLETE
// Copyright 2024 mecanum_pico Development
// SPDX-License-Identifier: Apache-2.0
//
// Serial communication layer for the Raspberry Pi Pico (USB-CDC).
// Wire protocol (Sprint 2):
//   Host → Pico : "m <fl> <fr> <rl> <rr>\r"   (signed int tick counts per loop)
//   Pico → Host : "e <fl> <fr> <rl> <rr>\r\n"  (cumulative encoder ticks)
//   Host → Pico : "r\r"                          (reset encoder counters)
//   Pico → Host : "OK\r\n"                        (ack for reset)

#ifndef MECANUM_PICO__PICO_COMMS_HPP_
#define MECANUM_PICO__PICO_COMMS_HPP_

#include <sstream>
#include <iostream>
#include <string>
#include <libserial/SerialPort.h>

// ---------------------------------------------------------------------------
// Baud-rate helper (identical to original arduino_comms.hpp)
// ---------------------------------------------------------------------------
static LibSerial::BaudRate convert_baud_rate(int baud_rate)
{
  switch (baud_rate) {
    case 1200:   return LibSerial::BaudRate::BAUD_1200;
    case 1800:   return LibSerial::BaudRate::BAUD_1800;
    case 2400:   return LibSerial::BaudRate::BAUD_2400;
    case 4800:   return LibSerial::BaudRate::BAUD_4800;
    case 9600:   return LibSerial::BaudRate::BAUD_9600;
    case 19200:  return LibSerial::BaudRate::BAUD_19200;
    case 38400:  return LibSerial::BaudRate::BAUD_38400;
    case 57600:  return LibSerial::BaudRate::BAUD_57600;
    case 115200: return LibSerial::BaudRate::BAUD_115200;
    case 230400: return LibSerial::BaudRate::BAUD_230400;
    default:
      std::cerr << "[PicoComms] Unsupported baud rate " << baud_rate
                << " — defaulting to 115200\n";
      return LibSerial::BaudRate::BAUD_115200;
  }
}

// ---------------------------------------------------------------------------
// PicoComms
// ---------------------------------------------------------------------------
class PicoComms
{
public:
  PicoComms() = default;

  // -------------------------------------------------------------------------
  // Connection management
  // -------------------------------------------------------------------------

  void connect(const std::string & serial_device, int32_t baud_rate, int32_t timeout_ms)
  {
    timeout_ms_ = timeout_ms;
    serial_conn_.Open(serial_device);
    serial_conn_.SetBaudRate(convert_baud_rate(baud_rate));
  }

  void disconnect()
  {
    serial_conn_.Close();
  }

  bool connected() const
  {
    return serial_conn_.IsOpen();
  }

  // -------------------------------------------------------------------------
  // Low-level send / receive
  // -------------------------------------------------------------------------

  /**
   * @brief Send a raw string and read the next line response.
   * @param msg_to_send  String to transmit (must include terminator, e.g. "\r").
   * @param print_output If true, log sent/received strings to stdout.
   * @return             The response line (up to and including '\n'), or "" on timeout.
   */
  virtual std::string send_msg(const std::string & msg_to_send, bool print_output = false)
  {
    serial_conn_.FlushIOBuffers();
    serial_conn_.Write(msg_to_send);

    std::string response;
    try {
      serial_conn_.ReadLine(response, '\n', timeout_ms_);
    } catch (const LibSerial::ReadTimeout &) {
      std::cerr << "[PicoComms] ReadLine timed out.\n";
    }
    if (print_output) {
      std::cout << "[PicoComms] Sent: " << msg_to_send << "  Recv: " << response << "\n";
    }
    return response;
  }

  /** @brief Send the wake/sync byte (equivalent to old sendEmptyMsg). */
  void send_empty_msg()
  {
    send_msg("\r");
  }

  // -------------------------------------------------------------------------
  // 4-wheel motor command
  // -------------------------------------------------------------------------

  /**
   * @brief Send velocity commands to all 4 motors.
   *
   * Values are float rad/s targets.
   * The Pico PID loop converts these to PWM duty cycles locally.
   *
   * @param fl Front-left  motor [rad/s].
   * @param fr Front-right motor [rad/s].
   * @param rl Rear-left   motor [rad/s].
   * @param rr Rear-right  motor [rad/s].
   */
  void set_motor_values(int fl, int fr, int rl, int rr)
  {
    std::stringstream ss;
    ss << "m " << fl << " " << fr << " " << rl << " " << rr << "\r";
    send_msg(ss.str());
  }

  // -------------------------------------------------------------------------
  // 4-wheel encoder read
  // -------------------------------------------------------------------------

  /**
   * @brief Request and parse cumulative encoder tick counts from the Pico.
   *
   * Sends "e\r" and parses the response "e <fl> <fr> <rl> <rr>\r\n".
   *
   * @param[out] fl  Front-left  cumulative encoder ticks.
   * @param[out] fr  Front-right cumulative encoder ticks.
   * @param[out] rl  Rear-left   cumulative encoder ticks.
   * @param[out] rr  Rear-right  cumulative encoder ticks.
   * @return true on successful parse, false on timeout or malformed response.
   */
  bool read_encoder_values(int & fl, int & fr, int & rl, int & rr)
  {
    std::string response = send_msg("e\r");
    return parse_encoder_response(response, fl, fr, rl, rr);
  }

  /**
   * @brief Parse an encoder response string of the form "e <fl> <fr> <rl> <rr>\r\n".
   *
   * This method is public and virtual so it can be unit-tested without a real serial port.
   *
   * @return true if exactly 5 tokens were parsed and the prefix is 'e'.
   */
  virtual bool parse_encoder_response(
    const std::string & line, int & fl, int & fr, int & rl, int & rr)
  {
    char prefix = 0;
    int parsed = std::sscanf(line.c_str(), "%c %d %d %d %d", &prefix, &fl, &fr, &rl, &rr);
    return parsed == 5 && prefix == 'e';
  }

  // -------------------------------------------------------------------------
  // IMU read (accelerometer + gyroscope)
  // -------------------------------------------------------------------------

  /**
   * @brief Request and parse IMU accel+gyro values from the Pico.
   *
   * Sends "i\r" and parses the response "ax ay az gx gy gz\n" (no prefix char,
   * see pico_firmware/src/main.cpp 'i' command).
   *
   * Units as returned by the firmware: acceleration in [g], angular rate in [deg/s].
   * Caller is responsible for converting to SI units (m/s^2, rad/s) for ROS.
   *
   * @return true on successful parse, false on timeout or malformed response.
   */
  bool read_imu_values(
    double & ax, double & ay, double & az,
    double & gx, double & gy, double & gz)
  {
    std::string response = send_msg("i\r");
    return parse_imu_response(response, ax, ay, az, gx, gy, gz);
  }

  /**
   * @brief Parse an IMU response string of the form "ax ay az gx gy gz\r\n".
   *
   * This method is public and virtual so it can be unit-tested without a real serial port.
   *
   * @return true if exactly 6 tokens were parsed.
   */
  virtual bool parse_imu_response(
    const std::string & line,
    double & ax, double & ay, double & az,
    double & gx, double & gy, double & gz)
  {
    int parsed = std::sscanf(
      line.c_str(), "%lf %lf %lf %lf %lf %lf", &ax, &ay, &az, &gx, &gy, &gz);
    return parsed == 6;
  }

  // -------------------------------------------------------------------------
  // Reset encoders
  // -------------------------------------------------------------------------

  /** @brief Send reset command. Pico clears all encoder counters and responds "OK\n". */
  void reset_encoders()
  {
    send_msg("r\r");
  }

private:
  LibSerial::SerialPort serial_conn_;
  int timeout_ms_ = 1000;
};

#endif  // MECANUM_PICO__PICO_COMMS_HPP_
