// Minimal PicoComms abstraction for native unit tests (moved to test/include)
#pragma once

#include <string>
#include <sstream>
#include <vector>
#include <cstdlib>

class PicoComms {
public:
    virtual ~PicoComms() = default;
    // send_msg should be overridden by mocks; default returns empty
    virtual std::string send_msg(const std::string& msg_to_send, bool /*print_output*/ = false) { (void)msg_to_send; return std::string(); }

    void set_motor_values(int fl, int fr, int rl, int rr) {
        std::ostringstream os;
        os << "m " << fl << " " << fr << " " << rl << " " << rr << "\r";
        send_msg(os.str(), false);
    }

    void read_encoder_values(int& fl, int& fr, int& rl, int& rr) {
        send_msg("e\r", false);
        fl = fr = rl = rr = 0;
    }

    bool parse_encoder_response(const std::string& s, int& fl, int& fr, int& rl, int& rr) {
        if (s.empty()) return false;
        if (s.size() < 2) return false;
        if (s[0] != 'e') return false;
        std::istringstream is(s.substr(1));
        std::vector<int> vals;
        int v;
        while (is >> v) vals.push_back(v);
        if (vals.size() != 4) return false;
        fl = vals[0]; fr = vals[1]; rl = vals[2]; rr = vals[3];
        return true;
    }
};
