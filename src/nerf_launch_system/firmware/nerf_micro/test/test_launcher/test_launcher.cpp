// test_launcher.cpp
// Launcher-Tests — selbstständiger ArduinoMock (kein adrianaxente/arduino-mock)
// Testet Hardware-Interaktion via GMock: delay(), pinMode(), digitalWrite()

#include <Arduino.h>  // ← test/mock_launcher/Arduino.h
#include <gmock/gmock.h>
#include <gtest/gtest.h>

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
#include "Launcher.cpp"
#include "SerialOutput.cpp"
#include "TiltController.cpp"

using ::testing::_;
using ::testing::AtLeast;
using ::testing::Ne;
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
    void advanceMs(uint32_t ms) {
        mock->addMillisRaw(ms);
    }
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
// TEST 8: testShot() waehrend einer laufenden Sequenz wird abgewiesen
// (Regression: vorher ueberschrieb ein zweiter Aufruf _manualState/
// _manualTimer kommentarlos und korrumpierte die laufende Sequenz.)
// ============================================================
TEST_F(LauncherTest, TestShot_RejectsWhenBusy) {
    Launcher launcher;
    launcher.begin();

    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    launcher.testShot(500);  // startet TEST_SHOT_PUSH
    launcher.testShot(500);  // muss abgewiesen werden -> keine weiteren Servo-Calls
}

// ============================================================
// TEST 9: dangerousShot() waehrend einer laufenden Sequenz wird abgewiesen
// ============================================================
TEST_F(LauncherTest, DangerousShot_RejectsWhenBusy) {
    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    launcher.dangerousShot(500);
    launcher.dangerousShot(500);  // muss abgewiesen werden
}

// ============================================================
// TEST 10: nudge() waehrend einer laufenden Sequenz wird abgewiesen
// ============================================================
TEST_F(LauncherTest, Nudge_RejectsWhenBusy) {
    Launcher launcher;
    launcher.begin();

    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    launcher.nudge(true);
    launcher.nudge(false);  // muss abgewiesen werden -> Servo faehrt NICHT in Gegenrichtung
}

// ============================================================
// TEST 11: Der Busy-Guard gilt methodenuebergreifend, nicht nur pro Methode
// ============================================================
TEST_F(LauncherTest, CrossMethod_BusyRejected) {
    Launcher launcher;
    launcher.begin();
    launcher.getFSM().triggerArming();
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    launcher.testShot(500);       // startet eine Sequenz
    launcher.dangerousShot(500);  // muss abgewiesen werden (busy)
    launcher.nudge(true);         // muss abgewiesen werden (busy)
}

// ============================================================
// TEST 12: millis()-Rollover waehrend einer manuellen Sequenz darf
// deren Abschluss nicht verhindern (rollover-sichere Differenzpruefung).
// ============================================================
TEST_F(LauncherTest, MillisRollover_ManualSequenceStillCompletes) {
    Launcher launcher;
    launcher.begin();
    mock->setMillisRaw(UINT32_MAX - 50);

    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    launcher.nudge(true);  // _manualTimer wraps around UINT32_MAX
    testing::Mock::VerifyAndClearExpectations(&launcher.getShot());

    // Ueberschreitet den Wraparound-Punkt und die erste (200ms Nudge-Out) Deadline
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);  // NUDGE_OUT -> NUDGE_CENTER
    advanceMs(250);
    launcher.update();
    testing::Mock::VerifyAndClearExpectations(&launcher.getShot());

    // Erreicht die zweite (50ms Center) Deadline -> Detach
    EXPECT_CALL(launcher.getShot(), detach()).Times(1);
    advanceMs(60);
    launcher.update();
}

// ============================================================
// Fixture: TiltController (T_POS / setPosition auto-detach bugfix)
// ============================================================
class TiltControllerTest : public ::testing::Test {
protected:
    ArduinoMock* mock;

    void SetUp() override {
        mock = arduinoMockInstanceNice();
        mock->setMillisRaw(0);
    }
    void TearDown() override {
        releaseArduinoMock();
    }
    void advanceMs(uint32_t ms) {
        mock->addMillisRaw(ms);
    }
};

// ============================================================
// TEST 8: setPosition() haelt den Wert und detached erst nach TILT_HOLD_MS
// (Regression: vorher setzte setPosition() sofort State::IDLE, sodass
// update() nie detachte und der Servo dauerhaft bestromt blieb.)
// ============================================================
TEST_F(TiltControllerTest, SetPosition_HoldsThenAutoDetachesAfterHoldWindow) {
    TiltController tilt(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);

    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(1600)).Times(1);
    tilt.setPosition(1600);
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    // Kurz vor der Deadline: noch kein Detach
    EXPECT_CALL(tilt.getServo(), detach()).Times(0);
    advanceMs(Config::TILT_HOLD_MS - 1);
    tilt.update();
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    // Deadline erreicht: Detach feuert
    EXPECT_CALL(tilt.getServo(), detach()).Times(1);
    advanceMs(1);
    tilt.update();
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());
}

// ============================================================
// TEST 9: setPosition() darf vor dem Detach NICHT auf _neutralUs
// zurueckschreiben (sonst wuerde ein zu testender Kandidatenwert
// stillschweigend ueberschrieben).
// ============================================================
TEST_F(TiltControllerTest, SetPosition_DoesNotRewriteNeutralBeforeDetach) {
    TiltController tilt(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);

    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    // Am wenigsten spezifischer Matcher zuerst: jeder ANDERE Wert als 1600 ist ein Fehler.
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(Ne(1600))).Times(0);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(1600)).Times(1);
    EXPECT_CALL(tilt.getServo(), detach()).Times(1);

    tilt.setPosition(1600);
    advanceMs(Config::TILT_HOLD_MS);
    tilt.update();
}

// ============================================================
// TEST 10: millis()-Rollover waehrend der Haltezeit darf das Detach
// nicht verhindern (rollover-sichere Differenzpruefung statt now >= deadline).
// ============================================================
TEST_F(TiltControllerTest, SetPosition_MillisRollover_StillDetachesCorrectly) {
    TiltController tilt(Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT);
    mock->setMillisRaw(UINT32_MAX - 100);

    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(1600)).Times(1);
    tilt.setPosition(1600);  // _stateEndTime wraps around UINT32_MAX
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    // Ueberschreitet den Wraparound-Punkt, aber noch weit vor der 8s-Deadline
    EXPECT_CALL(tilt.getServo(), detach()).Times(0);
    advanceMs(200);
    tilt.update();
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    // Jetzt (im gewrappten Zeitraum) ueber die Deadline hinaus
    EXPECT_CALL(tilt.getServo(), detach()).Times(1);
    advanceMs(Config::TILT_HOLD_MS);
    tilt.update();
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());
}

// ============================================================
// Entry Point
// ============================================================
int main(int argc, char** argv) {
    ::testing::InitGoogleMock(&argc, argv);
    return RUN_ALL_TESTS();
}
