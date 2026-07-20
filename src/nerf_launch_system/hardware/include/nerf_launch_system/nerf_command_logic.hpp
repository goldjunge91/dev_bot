/**
 * @file nerf_command_logic.hpp
 * @brief Reine, ROS-/I/O-freie Kommando-Erzeugung für den Nerf Launcher
 *
 * Kapselt die Sequenzierung, die früher inline in NerfSystem::write() lag
 * (Tilt UP/DN-Pulse, SHOT-Einmal-Trigger), als pure Funktionen. Testbar
 * ohne Serial/ROS — siehe test/test_nerf_command_logic.cpp.
 */
#ifndef NERF_LAUNCH_SYSTEM_NERF_COMMAND_LOGIC_HPP
#define NERF_LAUNCH_SYSTEM_NERF_COMMAND_LOGIC_HPP

#include <optional>
#include <string>

namespace nerf_launch_system {

/**
 * @struct TiltStep
 * @brief Ergebnis eines Tilt-Integrationsschritts
 */
struct TiltStep {
    std::string command;  ///< Seriell zu sendendes Kommando, z.B. "UP 100"
    double new_tilt_pos;  ///< Neuer hw_states_.tilt_pos Wert nach diesem Schritt
};

/**
 * @brief Berechnet den nächsten Tilt-Integrationsschritt (UP/DN-Puls)
 *
 * Clampt target_pos auf [tilt_min, tilt_max], vergleicht mit current_pos und
 * gibt bei Bedarf einen einzelnen UP/DN-Schritt zurück, der current_pos um
 * `step` in Richtung target_pos verschiebt (ohne über das Ziel hinaus).
 * Unterhalb von `deadband` wird kein Kommando erzeugt (Servo bereits nah
 * genug am Ziel).
 *
 * @return std::nullopt wenn |target - current| <= deadband, sonst der
 *         nächste Schritt.
 */
std::optional<TiltStep> make_tilt_command(double target_pos,
                                          double current_pos,
                                          double tilt_min,
                                          double tilt_max,
                                          double step = 0.05,
                                          double deadband = 0.01,
                                          int duration_ms = 100);

/**
 * @brief Erzeugt bei Bedarf einen einmaligen SHOT-Befehl
 *
 * `shooter_cmd` > 0 löst genau einmal "SHOT <power>" aus (power = trunc.
 * shooter_cmd als int); solange shooter_cmd > 0 bleibt, wird nicht erneut
 * gefeuert (pusher_active bleibt true). Erst wenn shooter_cmd <= 0 fällt,
 * wird pusher_active zurückgesetzt und der nächste positive Wert löst
 * wieder genau einen SHOT aus.
 *
 * @param pusher_active Trigger-Zustand zwischen Aufrufen — vom Aufrufer
 *        gehalten (i.d.R. NerfSystem::pusher_active_).
 * @return std::nullopt wenn kein neuer SHOT ausgelöst werden soll.
 */
std::optional<std::string> make_shot_command(double shooter_cmd, bool &pusher_active);

}  // namespace nerf_launch_system

#endif  // NERF_LAUNCH_SYSTEM_NERF_COMMAND_LOGIC_HPP
