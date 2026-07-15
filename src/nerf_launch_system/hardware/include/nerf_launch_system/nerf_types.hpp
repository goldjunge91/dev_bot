/**
 * @file nerf_types.hpp
 * @brief Datentypen für das Nerf Launcher Hardware Interface
 *
 * Definiert die Structs für Command- und State-Werte der Nerf Joints.
 * Header-Only – keine .cpp nötig.
 */
#ifndef NERF_LAUNCH_SYSTEM_NERF_TYPES_HPP
#define NERF_LAUNCH_SYSTEM_NERF_TYPES_HPP

namespace nerf_launch_system {

/**
 * @struct NerfJoints
 * @brief Befehle an die Hardware (Command Interface)
 *
 * Diese Werte werden von Controllern gesetzt und in write() an Hardware gesendet.
 */
struct NerfJoints {
    double tilt_pos = 0.0;     // Tilt Servo Position in Radiant
    double shooter_pos = 0.0;  // Schuss: Flywheel Power % (>0 = SHOT, 0 = kein Schuss)
    double arming_pos = 0.0;   // Arming Status (>0.5 = Armed, <0.5 = Disarmed)
};

/**
 * @struct NerfJointStates
 * @brief Zustand der Hardware (State Interface)
 *
 * Diese Werte werden in read() aktualisiert und von Controllern gelesen.
 * shooter_pos/arming_pos: Open-Loop, Commands werden gespiegelt (keine
 * echten Encoder). tilt_pos ist die Ausnahme: write() integriert ihn
 * inkrementell entlang der gesendeten UP/DN-Pulse (kein Mirror in read()).
 */
struct NerfJointStates {
    double tilt_pos = 0.0;     // Aktuelle Tilt Position (inkrementell in write() integriert)
    double shooter_pos = 0.0;  // Schuss: gespiegelter Wert (Open-Loop)
    double arming_pos = 0.0;   // Arming Status
    // dart_pusher_joint hat keinen echten Encoder (Open-Loop, nur velocity-Kommando).
    // Ohne eigene position-State-Interface meldet joint_state_broadcaster NaN fuer
    // dieses Joint, was robot_state_publisher als kaputte TF fuer pusher_servo_part
    // weiterreicht. Diese Position wird in read() aus shooter_pos integriert — rein
    // fuer eine gueltige, sich bewegende TF/RViz-Darstellung, nicht physikalisch kalibriert.
    double dart_pusher_pos = 0.0;
};

}  // namespace nerf_launch_system

#endif  // NERF_LAUNCH_SYSTEM_NERF_TYPES_HPP
