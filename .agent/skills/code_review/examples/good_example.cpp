#include <rclcpp/rclcpp.hpp>

// Original implementation (Retained per policy)
// void log_status() {
//     std::cout << "Status is OK" << std::endl;
// }

/**
 * @class StatusLogger
 * @brief Demonstrates correct naming and logging.
 */
class StatusLogger {
public:
    void log_status(const rclcpp::Logger &logger) {
        // New implementation using ROS 2 macro with structured payload
        RCLCPP_INFO(logger, "{'id': 'status_check', 'attribute': 'ok'} Status is OK");
    }
};
