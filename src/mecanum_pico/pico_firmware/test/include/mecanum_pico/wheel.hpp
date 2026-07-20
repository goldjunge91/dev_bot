// Minimal Wheel model for native unit tests (moved to test/include)
#pragma once

#include <cmath>
#include <string>

struct Wheel {
    std::string name;
    int32_t enc;
    double cmd;
    double pos;
    double vel;
    double rads_per_count;

    Wheel() : name(""), enc(0), cmd(0.0), pos(0.0), vel(0.0), rads_per_count(0.0) {}
    Wheel(const std::string &n, int counts_per_rev) :
        name(n), enc(0), cmd(0.0), pos(0.0), vel(0.0) {
        const double PI = std::acos(-1.0);
        if (counts_per_rev != 0) {
            rads_per_count = (2.0 * PI) / (double)counts_per_rev;
        } else {
            rads_per_count = 0.0;
        }
    }

    void setup(const std::string &n, int counts_per_rev) {
        name = n;
        const double PI = std::acos(-1.0);
        if (counts_per_rev != 0) {
            rads_per_count = (2.0 * PI) / (double)counts_per_rev;
        } else {
            rads_per_count = 0.0;
        }
    }

    double calc_enc_angle() const {
        return (double)enc * rads_per_count;
    }
};
