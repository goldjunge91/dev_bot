#ifndef NERF_MICRO_HELP_H
#define NERF_MICRO_HELP_H

#include "../../include/Config.h"
#include "SerialOutput.h"

#include <Arduino.h>

class Help {
public:
    static void printHelp();

    /**
     * @brief Gibt die aktuellen Hardware-Konfigurationswerte aus.
     * @param shotZero    Aktueller Shot-Neutralwert (us)
     * @param tiltNeutral Aktueller Tilt-Neutralwert (us)
     * @param shotDur     Aktuelle Schussdauer (ms)
     */
    static void printConfig(int shotZero, int tiltNeutral, int shotDur);

    static void printStartup(int shotZero, int tiltNeutral, int shotDur);
};

#endif  // NERF_MICRO_HELP_H
