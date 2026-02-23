#ifndef NERF_MICRO_HELP_H
#define NERF_MICRO_HELP_H

#include "../../include/Config.h"
#include "Launcher.h"
#include "SerialOutput.h"
#include "TiltController.h"

#include <Arduino.h>
#include <Servo.h>  // Arduino-Bibliothek zur Ansteuerung von Servomotoren

// Globale Instanzen der Hardware-Controller aus der main.cpp
extern Launcher nerf;
extern TiltController tiltCtrl;

/**
 * @class Help
 * @brief Hilfsklasse zur Ausgabe von Systeminformationen und Menüs (Terminal).
 *
 * Kapselt alle Konsolen-Ausgaben, um die Übersichtlichkeit der Hauptdatei zu wahren.
 */
class Help {
public:
    /**
     * @brief Gibt die Liste aller verfügbaren Befehle über die Serielle Schnittstelle aus.
     */
    static void printHelp();

    /**
     * @brief Gibt die aktuellen Hardware-Konfigurationswerte und Offset-Einstellungen aus.
     */
    static void printConfig();

    /**
     * @brief Zeigt das Logo und die Systemparameter während des Bootvorgangs an.
     */
    static void printStartup();
};

#endif  // NERF_MICRO_HELP_H
