// test_comms.cpp
// Comms-Tests — Dispatch-Korrektheit, Loopback-Schutz, Pufferueberlauf.
// Vorher gab es fuer Comms in keiner Umgebung Testabdeckung.

#include <Arduino.h>  // ← test/mock_comms/Arduino.h
#include <gmock/gmock.h>
#include <gtest/gtest.h>

// ── Globale Instanzen ────────────────────────────────────────
Stream Serial;
Stream Serial1;

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
#include "Comms.cpp"
#include "FiringFSM.cpp"
#include "Help.cpp"
#include "Launcher.cpp"
#include "SerialOutput.cpp"
#include "TiltController.cpp"

using ::testing::_;
using ::testing::HasSubstr;

// ============================================================
// Fixture
// ============================================================
class CommsTest : public ::testing::Test {
protected:
    ArduinoMock* mock;
    Launcher launcher;
    TiltController tilt{Config::PIN_TILT, Config::TILT_NEUTRAL_DEFAULT};
    Comms comms{launcher, tilt, Serial};

    void SetUp() override {
        mock = arduinoMockInstanceNice();
        mock->setMillisRaw(0);
        launcher.begin();
        Serial.clearOutput();
        Serial1.clearOutput();
    }
    void TearDown() override {
        releaseArduinoMock();
    }

    // Simuliert das Eintreffen einer Zeile ueber den Stream + Comms::update().
    void feed(const char* line) {
        Serial.feed(line);
        Serial.feed("\n");
        comms.update();
    }

    void arm() {
        feed("ARM");
        launcher.update();  // IDLE -> ARMING (entry: delay)
        launcher.update();  // ARMING -> ARMED
        ASSERT_TRUE(launcher.getFSM().isArmed());
    }
};

// ============================================================
// Dispatch: Sicherheits-/Systembefehle
// ============================================================
TEST_F(CommsTest, Dispatch_Arm_TriggersArming) {
    feed("ARM");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::ARMING);
}

TEST_F(CommsTest, Dispatch_Disarm_ClearsArmedFlag) {
    arm();
    feed("DISARM");
    launcher.update();
    EXPECT_FALSE(launcher.getFSM().isArmed());
}

TEST_F(CommsTest, Dispatch_Stop_IsAliasForDisarm) {
    arm();
    feed("STOP");
    launcher.update();
    EXPECT_FALSE(launcher.getFSM().isArmed());
}

TEST_F(CommsTest, Dispatch_Status_ReportsArmedState) {
    Serial.clearOutput();
    feed("STATUS");
    EXPECT_THAT(Serial.output(), HasSubstr("STATUS: DISARMED"));

    arm();
    Serial.clearOutput();
    feed("STATUS");
    EXPECT_THAT(Serial.output(), HasSubstr("STATUS: ARMED"));
}

// ============================================================
// Dispatch: Feuer-Befehle
// ============================================================
TEST_F(CommsTest, Dispatch_Shot_ExplicitPower_TransitionsToSpinningUp) {
    arm();
    feed("SHOT 60");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::SPINNING_UP);
}

TEST_F(CommsTest, Dispatch_Shot_NoArg_DefaultsToPower5) {
    arm();
    feed("SHOT");  // val<=0 -> Default 5, muss trotzdem feuern
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::SPINNING_UP);
}

TEST_F(CommsTest, Dispatch_TestEsc_StartsFlywheels) {
    arm();
    feed("TEST_ESC 30");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::ESC_TEST);
}

TEST_F(CommsTest, Dispatch_Pwm_RequiresArmed) {
    feed("PWM 1500");  // nicht armed -> darf ESCs nicht anhaengen
    EXPECT_FALSE(launcher.getLeftESC().attached());
}

TEST_F(CommsTest, Dispatch_Pwm_WhenArmed_WritesRawPwm) {
    arm();
    EXPECT_CALL(launcher.getLeftESC(), writeMicroseconds(1500)).Times(1);
    EXPECT_CALL(launcher.getRightESC(), writeMicroseconds(1500)).Times(1);
    feed("PWM 1500");
}

TEST_F(CommsTest, Dispatch_Cal_EntersCalibrating) {
    arm();
    feed("CAL");
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::CALIBRATING);
}

TEST_F(CommsTest, Dispatch_CalMaxMinTest_AreNowUnknownCommands) {
    Serial.clearOutput();
    feed("CAL_MAX");
    EXPECT_THAT(Serial.output(), HasSubstr("ERR: Unknown"));

    Serial.clearOutput();
    feed("CAL_MIN");
    EXPECT_THAT(Serial.output(), HasSubstr("ERR: Unknown"));

    Serial.clearOutput();
    feed("CAL_TEST");
    EXPECT_THAT(Serial.output(), HasSubstr("ERR: Unknown"));
}

TEST_F(CommsTest, Dispatch_Nf_Nb_MoveShotServo) {
    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    feed("NF");
}

TEST_F(CommsTest, Dispatch_TestShot_StartsPushSequence) {
    EXPECT_CALL(launcher.getShot(), attach(_, _, _)).Times(1);
    EXPECT_CALL(launcher.getShot(), writeMicroseconds(_)).Times(1);
    feed("TEST_SHOT 500");
}

TEST_F(CommsTest, Dispatch_DangerousShot_RequiresArmed) {
    Serial.clearOutput();
    feed("DANGEROUS_SHOT 500");
    EXPECT_THAT(Serial.output(), HasSubstr("ERR: Arm first!"));
}

TEST_F(CommsTest, Dispatch_ZeroS_SetsShotNeutral) {
    feed("ZERO_S 1500");
    EXPECT_EQ(launcher.getShotZero(), 1500);
}

TEST_F(CommsTest, Dispatch_SetShot_SetsDuration) {
    feed("SET_SHOT 3000");
    EXPECT_EQ(launcher.getShotDur(), 3000);
}

// ============================================================
// Dispatch: Tilt-Befehle
// ============================================================
TEST_F(CommsTest, Dispatch_Up_ExplicitMs_MovesTilt) {
    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(Config::SV_MAX_US)).Times(1);
    feed("UP 500");
}

TEST_F(CommsTest, Dispatch_Dn_NoArg_DefaultsTo200ms) {
    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(Config::SV_MIN_US)).Times(1);
    feed("DN");  // val<=0 -> Default 200ms, muss trotzdem bewegen
}

TEST_F(CommsTest, Dispatch_Tu_Td_NudgeTilt) {
    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(_)).Times(1);
    feed("TU");
}

TEST_F(CommsTest, Dispatch_ZeroT_SetsTiltNeutral) {
    feed("ZERO_T 1500");
    EXPECT_EQ(tilt.getNeutral(), 1500);
}

TEST_F(CommsTest, Dispatch_TPos_HoldsPosition) {
    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(1600)).Times(1);
    feed("T_POS 1600");
}

// ============================================================
// Dispatch: Sonstiges
// ============================================================
TEST_F(CommsTest, Dispatch_Save_PrintsConfig) {
    Serial.clearOutput();
    feed("SAVE");
    EXPECT_THAT(Serial.output(), HasSubstr("CURRENT CONFIG"));
}

TEST_F(CommsTest, Dispatch_Help_PrintsCommandList) {
    Serial.clearOutput();
    feed("HELP");
    EXPECT_THAT(Serial.output(), HasSubstr("COMMAND LIST"));
}

TEST_F(CommsTest, Dispatch_UnknownMultiCharCommand_ReportsError) {
    Serial.clearOutput();
    feed("FOOBAR");
    EXPECT_THAT(Serial.output(), HasSubstr("ERR: Unknown"));
}

TEST_F(CommsTest, Dispatch_SingleStrayChar_IsSilentlySwallowed) {
    Serial.clearOutput();
    feed("x");
    EXPECT_THAT(Serial.output(), ::testing::Not(HasSubstr("ERR: Unknown")));
}

// ============================================================
// Loopback-Schutz
// ============================================================
TEST_F(CommsTest, LoopbackProtection_BlocksEchoedPrefixes) {
    static const char* const kEchoLines[] = {
        ">some prompt",
        "ERR: something",
        "OK: something",
        "STATUS: ARMED",
        "NERF OS PRO",
        "---divider---",
        "SHOT ZERO: 1430",
        "TILT ZERO: 1430",
        "err lowercase"  // Case-insensitivitaet
    };
    for (const char* line : kEchoLines) {
        FiringState before = launcher.getFSM().getCurrentState();
        bool armedBefore = launcher.getFSM().isArmed();
        feed(line);
        EXPECT_EQ(launcher.getFSM().getCurrentState(), before) << "line: " << line;
        EXPECT_EQ(launcher.getFSM().isArmed(), armedBefore) << "line: " << line;
    }
}

// ============================================================
// Pufferueberlauf
// ============================================================
TEST_F(CommsTest, BufferOverflow_DropsLineAndRecovers) {
    // > kBufferSize (40) Zeichen, terminiert wie eine reale (verrauschte) Zeile
    std::string longLine(60, 'A');
    Serial.feed(longLine.c_str());
    Serial.feed("\n");  // beendet die Garbage-Zeile -> _overflow wird zurueckgesetzt
    comms.update();
    EXPECT_THAT(Serial.output(), HasSubstr("Line too long"));

    // Eine eigene, separat terminierte Folgezeile muss wieder korrekt ankommen
    Serial.clearOutput();
    feed("ARM");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::ARMING);
}

TEST_F(CommsTest, BufferOverflow_WithoutOwnTerminator_AlsoDiscardsGluedFollowupUntilNextNewline) {
    // Garbage OHNE eigenen Terminator, direkt gefolgt von "ARM\n" auf derselben
    // ungeteilten Zeile: die Resynchronisation erfolgt erst am naechsten \n, daher
    // wird "ARM" hier mitverworfen. Dokumentiert die Design-Grenze: Recovery
    // braucht einen Zeilenumbruch, kann nicht mitten in der Zeile erfolgen.
    std::string glued(60, 'A');
    glued += "ARM\n";
    Serial.feed(glued.c_str());
    comms.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::IDLE);

    // Ab hier ist der Puffer wieder synchron: ein sauberer Folgebefehl funktioniert.
    Serial.clearOutput();
    feed("ARM");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::ARMING);
}

// ============================================================
// Wire-Protokoll-Regressionsschutz: exakt die Strings, die die
// ROS2-Hardware-Schnittstelle sendet (nerf_command_logic.cpp).
// ============================================================
TEST_F(CommsTest, WireProtocol_Ros2Commands_DispatchCorrectly) {
    feed("ARM");
    launcher.update();
    launcher.update();
    ASSERT_TRUE(launcher.getFSM().isArmed());

    EXPECT_CALL(tilt.getServo(), attach(_, _, _)).Times(1);
    EXPECT_CALL(tilt.getServo(), writeMicroseconds(Config::SV_MAX_US)).Times(1);
    feed("UP 500");
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    EXPECT_CALL(tilt.getServo(), writeMicroseconds(Config::SV_MIN_US)).Times(1);
    feed("DN 500");
    testing::Mock::VerifyAndClearExpectations(&tilt.getServo());

    feed("SHOT 60");
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::SPINNING_UP);

    feed("DISARM");
    launcher.update();
    launcher.update();
    EXPECT_EQ(launcher.getFSM().getCurrentState(), FiringState::DISARMED);
}

// ============================================================
// Entry Point
// ============================================================
int main(int argc, char** argv) {
    ::testing::InitGoogleMock(&argc, argv);
    return RUN_ALL_TESTS();
}
