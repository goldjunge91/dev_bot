//
// Created by tozzi on 18.02.2026.
//

#ifndef COMMS_H
#define COMMS_H

#include "Launcher.h"
#include "TiltController.h"
#include <Arduino.h>

/**
 * @brief Handles serial communication and command dispatching.
 *
 * The Comms class listens to the provided Stream (usually Serial)
 * for incoming commands, parses them, and routes them to the
 * appropriate controller (Launcher or TiltController).
 */
class Comms {
private:
    Launcher &_launcher;
    TiltController &_tilt;
    Stream &_stream;
    String _buffer;

    /**
     * @brief Broadcasts a message to all connected serial ports.
     *
     * Sends the message to the main stream and optionally to a secondary
     * serial port if applicable (e.g. Serial and Serial1).
     *
     * @param msg The C-string message to send.
     */
    void broadcast(const char *msg);

    void broadcast(const __FlashStringHelper *msg);

public:
    /**
     * @brief Constructed the Comms object.
     *
     * @param l Reference to the Launcher controller.
     * @param t Reference to the TiltController.
     * @param s Reference to the Serial stream to listen to.
     */
    Comms(Launcher &l, TiltController &t, Stream &s);

    /**
     * @brief Reads available serial data and constructs commands.
     *
     * Should be called in the main loop. Accumulates characters until
     * a newline is received, then triggers execution.
     */
    void update();

    /**
     * @brief Parses and executes a single command line.
     *
     * @param line The command string to execute.
     */
    void execute(String line);
};

#endif // COMMS_H