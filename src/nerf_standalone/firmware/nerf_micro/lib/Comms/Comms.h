//
// Created by tozzi on 18.02.2026.
//

#ifndef COMMS_H
#define COMMS_H

#include "Launcher.h"
#include "TiltController.h"

#include <Arduino.h>

/**
 * @brief Behandelt die serielle Kommunikation und das Verteilen von Befehlen.
 *
 * Die Comms-Klasse "lauscht" auf dem übergebenen Stream (meistens `Serial` über USB
 * oder `Serial1` über die Raspberry Pi GPIO-Pins) auf eingehende Textbefehle, analysiert diese
 * und leitet sie an den entsprechenden Controller (Launcher oder TiltController) weiter.
 */
class Comms {
private:
    Launcher &_launcher;
    TiltController &_tilt;
    Stream &_stream;  // 'Stream' aus der Arduino-Bibliothek (Datenstrom, z.B. Serial)
    String _buffer;

    /**
     * @brief Sendet eine Nachricht an alle verbundenen seriellen Ports.
     *
     * Gibt die Nachricht auf dem Haupt-Stream (z.B. USB) aus und zusätzlich
     * auf dem sekundären seriellen Port (`Serial1`), falls verfügbar, sodass
     * Debugging und Raspberry Pi-Steuerung gleichzeitig Status-Updates erhalten.
     *
     * @param msg Die C-String (Text) Nachricht.
     */
    void broadcast(const char *msg);

    void broadcast(const __FlashStringHelper *msg);

public:
    /**
     * @brief Konstruktor für das Comms-Objekt.
     *
     * @param launcher Referenz auf den Haupt-Launcher (Schuss/Motoren).
     * @param tiltController Referenz auf den TiltController (Neigungsservo).
     * @param serialStream Referenz auf den seriellen Stream (z.B. Serial oder Serial1), auf den
     * gelauscht werden soll.
     */
    Comms(Launcher &launcher, TiltController &tiltController, Stream &serialStream);

    /**
     * @brief Liest verfügbare serielle Daten und baut daraus Befehlszeilen zusammen.
     *
     * Muss andauernd in der Hauptschleife (loop) aufgerufen werden. Sammelt einzelne
     * Zeichen, bis ein Zeilenumbruch (Enter) empfangen wird, und löst dann den Befehl aus.
     */
    void update();

    /**
     * @brief Analysiert und führt eine einzelne vollständige Befehlszeile aus.
     *
     * @param line Der als Text (String) empfangene Befehl (z. B. "SHOT 60").
     */
    void execute(String line);
};

#endif  // COMMS_H