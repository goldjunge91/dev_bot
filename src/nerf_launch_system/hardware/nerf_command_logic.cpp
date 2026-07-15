/**
 * @file nerf_command_logic.cpp
 * @brief Implementierung der reinen Nerf-Kommando-Erzeugung
 */
#include "nerf_launch_system/nerf_command_logic.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>

namespace nerf_launch_system {

namespace {
// snprintf in einen Stack-Puffer statt std::stringstream/std::to_string-
// Konkatenation: deterministisch, keine iostream-Locale-Maschinerie, im
// 100-Hz-write()-Pfad relevant (RT-Hygiene).
constexpr std::size_t kCommandBufSize = 24;
}  // namespace

std::optional<TiltStep> make_tilt_command(double target_pos,
                                          double current_pos,
                                          double tilt_min,
                                          double tilt_max,
                                          double step,
                                          double deadband,
                                          int duration_ms) {
    double clamped_target = std::clamp(target_pos, tilt_min, tilt_max);
    double delta = clamped_target - current_pos;

    if (std::abs(delta) <= deadband) {
        return std::nullopt;
    }

    char buf[kCommandBufSize];
    TiltStep result;
    if (delta > 0) {
        std::snprintf(buf, sizeof(buf), "UP %d", duration_ms);
        result.new_tilt_pos = std::min(current_pos + step, clamped_target);
    } else {
        std::snprintf(buf, sizeof(buf), "DN %d", duration_ms);
        result.new_tilt_pos = std::max(current_pos - step, clamped_target);
    }
    result.command = buf;
    return result;
}

std::optional<std::string> make_shot_command(double shooter_cmd, bool &pusher_active) {
    int shot_power = static_cast<int>(shooter_cmd);
    if (shot_power > 0 && !pusher_active) {
        pusher_active = true;
        char buf[kCommandBufSize];
        std::snprintf(buf, sizeof(buf), "SHOT %d", shot_power);
        return std::string(buf);
    }
    if (shot_power <= 0) {
        pusher_active = false;
    }
    return std::nullopt;
}

}  // namespace nerf_launch_system
