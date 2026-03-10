#include "nerf_launch_system/nerf_communication.hpp"

#include <gtest/gtest.h>

namespace nerf_launch_system {

TEST(TestNerfCommunication, reconnection_logic_test) {
    NerfCommunication comms;

    // We can't easily open a real port in CI/Tests without hardware
    // But we can check if it stores the parameters and if reconnect() doesn't crash

    std::string test_port = "/dev/ttyNonExistent";
    int32_t test_baud = 115200;

    // This will likely throw or fail, which is fine as we want to test the retry logic
    try {
        comms.connect(test_port, test_baud);
    } catch (...) {
        // Expected failure for non-existent port
    }

    EXPECT_FALSE(comms.connected());

    // Now verify that reconnect() at least tries to use the same port (we can't easily check
    // private members without hacks or friends) For now, we're testing that the code path is
    // accessible and robust
    comms.reconnect();
    EXPECT_FALSE(comms.connected());  // Still false as port doesn't exist
}

}  // namespace nerf_launch_system
