// test_launcher.cpp
// Launcher-Tests — selbstständiger ArduinoMock (kein adrianaxente/arduino-mock)
// Testet Hardware-Interaktion via GMock: delay(), pinMode(), digitalWrite()

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <Arduino.h>  // ← test/mock_launcher/Arduino.h

// ── Globale Instanzen ────────────────────────────────────────
SerialStub Serial;
SerialStub Serial1;

// ── ArduinoMock Singleton ────────────────────────────────────
static ArduinoMock* _instance = nullptr;

ArduinoMock* arduinoMockInstance() {
    if (!_instance) _instance = new ArduinoMock();
    return _instance;
}
ArduinoMock* arduinoMockInstanceNice() {
    if (!_instance) _instance = new ::testing::NiceMock<ArduinoMock>();
    return _instance;
}
void releaseArduinoMock() {
    delete _instance;
    _instance = nullptr;
}

// ── Quellen direkt einbinden ─────────────────────────────────
#include "FiringFSM.cpp"
#include "SerialOutput.cpp"
#include "TiltController.cpp"
#include "Launcher.cpp"

using ::testing::_;
using ::testing::AtLeast;
using ::testing::Return;

// ============================================================
// Fixture
// ============================================================
class LauncherTest : public ::testing::Test {
protected:
    ArduinoMock* mock;

    void SetUp() override {
        mock = arduinoMockInstanceNice();
        mock->setMillisRaw(0);
    }
    void TearDown() override {
        releaseArduinoMock();
    }
    void advanceMs(uint32_t ms) { mock->addMillisRaw(ms); }
};

// ============================================================
// TEST 1: begin() — sicherer Initialzustand, kein Crash
// ============================================================
TEST_F(LauncherTest, Begin_SafeState) {
    Launcher launcher;
    launcher.begin();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::IDLE);
    EXPECT_FALSE(launcher.getFSM().isArmed());
}

// ============================================================
// TEST 2: update() ohne Trigger — FSM bleibt in IDLE
// ============================================================
TEST_F(LauncherTest, Update_WithoutTrigger_StaysIdle) {
    Launcher launcher;
    launcher.begin();
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::IDLE);
}

// ============================================================
// TEST 3: ARM Sequenz — delay() wird aufgerufen (ARMING entry)
// ============================================================
TEST_F(LauncherTest, Arm_CallsDelay) {
    EXPECT_CALL(*mock, delay(_)).Times(AtLeast(1));

    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();  // IDLE -> ARMING (entry: delay)
    launcher.update();  // ARMING -> ARMED
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::ARMED);
    EXPECT_TRUE(launcher.getFSM().isArmed());
}

// ============================================================
// TEST 4: FIRE — Übergang nach SPINNING_UP
// ============================================================
TEST_F(LauncherTest, Fire_TransitionsToSpinningUp) {
    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    launcher.getFSM().triggerFire(60);
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::SPINNING_UP);
}

// ============================================================
// TEST 5: DISARM — isArmed wird false
// ============================================================
TEST_F(LauncherTest, Disarm_ClearsArmedFlag) {
    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    launcher.getFSM().triggerDisarming();
    launcher.update();
    EXPECT_FALSE(launcher.getFSM().isArmed());
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::DISARMED);
}

// ============================================================
// TEST 6: Konfiguration — setZS / setD
// ============================================================
TEST_F(LauncherTest, Config_ShotZeroAndDuration) {
    Launcher launcher;
    launcher.setZS(1500);
    EXPECT_EQ(launcher.getShotZero(), 1500);
    launcher.setD(3000);
    EXPECT_EQ(launcher.getShotDur(), 3000);
}

// ============================================================
// TEST 7: Auto-Disarm nach Inaktivität
// ============================================================
TEST_F(LauncherTest, AutoDisarm_AfterTimeout) {
    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    advanceMs(Config::AUTO_DISARM_MS + 1);
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::DISARMING);
    EXPECT_FALSE(launcher.getFSM().isArmed());
}

// ============================================================
// Entry Point
// ============================================================
int main(int argc, char** argv) {
    ::testing::InitGoogleMock(&argc, argv);
    return RUN_ALL_TESTS();
}
