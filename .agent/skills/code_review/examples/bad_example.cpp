#include <iostream>
#include <rclcpp/rclcpp.hpp>

// VIOLATION: Poor naming (not PascalCase)
class badClass {
public:
    // VIOLATION: Poor naming (not snake_case)
    void BadFunction() {
        // VIOLATION: std::cout used
        std::cout << "Starting process..." << std::endl;

        // VIOLATION: Missing structured payload
        RCLCPP_INFO(rclcpp::get_logger("bad"), "Process started without JSON-like payload");
    }
};
