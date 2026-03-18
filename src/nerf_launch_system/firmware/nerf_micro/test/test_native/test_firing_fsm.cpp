// Copyright 2026 Developer
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// test_firing_fsm.cpp
// GoogleTest für FiringFSM - 100% Zustandsüberdeckung
//
// Alle 11 FSM-Zustände und ihre Transitionen werden getestet:
// IDLE, ARMING, ARMED, DISARMING, DISARMED, SPINNING_UP,
// PUSHING, BRAKING, COOLDOWN, ESC_TEST, CALIBRATING

#include <gtest/gtest.h>

// FiringFSM direkt inkludieren (Header + Source)
// So umgehen wir das PlatformIO Library-System komplett
#include "FiringFSM.cpp"
#include "FiringFSM.h"

// === Mock millis() globale Variable ===
uint32_t _mock_millis_value = 0;

// === Mock Serial Instanzen ===
MockSerial Serial;
MockSerial Serial1;

// === Test Fixture ===
class FiringFSMTest : public ::testing::Test
{
protected:
  // Callback-Zähler
  int flywheelPowerCalls = 0;
  int lastFlywheelPower = -1;
  int shotServoCalls = 0;
  int lastShotServoUs = -1;
  int attachESCsCalls = 0;
  int detachESCsCalls = 0;
  int attachShotCalls = 0;
  int detachShotCalls = 0;
  int debugCalls = 0;
  std::string lastDebugMsg;

  // Static Instanz für Callbacks (GoogleTest Fixture Workaround)
  static FiringFSMTest * instance;

  // Static Callback Forwarder
  static void cbFlywheelPower(int pwr)
  {
    instance->flywheelPowerCalls++;
    instance->lastFlywheelPower = pwr;
  }
  static void cbShotServo(int us)
  {
    instance->shotServoCalls++;
    instance->lastShotServoUs = us;
  }
  static void cbAttachESCs()
  {
    instance->attachESCsCalls++;
  }
  static void cbDetachESCs()
  {
    instance->detachESCsCalls++;
  }
  static void cbAttachShot()
  {
    instance->attachShotCalls++;
  }
  static void cbDetachShot()
  {
    instance->detachShotCalls++;
  }
  static void cbDebug(const char * msg)
  {
    instance->debugCalls++;
    instance->lastDebugMsg = msg;
  }

  FiringFSM * fsm;

  void SetUp() override
  {
    instance = this;
    _mock_millis_value = 1000;      // Starte bei 1 Sekunde
    fsm = new FiringFSM(
      cbFlywheelPower,
      cbShotServo,
      cbAttachESCs,
      cbDetachESCs,
      cbAttachShot,
      cbDetachShot,
      cbDebug);
  }

  void TearDown() override
  {
    delete fsm;
  }

  // Helper: Einen FSM-Zyklus (evalTransition + evalState) ausführen
  void runCycle()
  {
    fsm->evalTransition();
    fsm->evalState();
  }

  // Helper: FSM in den ARMED-Zustand bringen
  void armFSM()
  {
    fsm->triggerArming();
    runCycle();      // -> ARMING
    advanceMillis(Config::ARM_DELAY_MS);
    runCycle();      // -> ARMED
  }

  // Helper: Zähler zurücksetzen
  void resetCounters()
  {
    flywheelPowerCalls = 0;
    lastFlywheelPower = -1;
    shotServoCalls = 0;
    lastShotServoUs = -1;
    attachESCsCalls = 0;
    detachESCsCalls = 0;
    attachShotCalls = 0;
    detachShotCalls = 0;
    debugCalls = 0;
    lastDebugMsg.clear();
  }
};

FiringFSMTest * FiringFSMTest::instance = nullptr;

// ============================================================================
// TEST 1: Initialzustand
// ============================================================================
TEST_F(FiringFSMTest, InitialState_IsIDLE) {
  EXPECT_EQ(fsm->getCurrentState(), FiringState::IDLE);
  EXPECT_FALSE(fsm->isArmed());
  EXPECT_FALSE(fsm->canFire());
}

// ============================================================================
// TEST 2: IDLE -> ARMING -> ARMED
// ============================================================================
TEST_F(FiringFSMTest, ArmingSequence_IdleToArmed) {
  // Trigger ARM
  fsm->triggerArming();
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMING);
  EXPECT_FALSE(fsm->isArmed());
  EXPECT_EQ(attachESCsCalls, 1);    // ESCs werden angehängt

  // Zu früh: noch nicht ARM_DELAY_MS vergangen
  advanceMillis(Config::ARM_DELAY_MS - 1);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMING);    // Bleibt ARMING

  // Jetzt ist die Zeit abgelaufen
  advanceMillis(1);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMED);
  EXPECT_TRUE(fsm->isArmed());
  EXPECT_TRUE(fsm->canFire());
}

// ============================================================================
// TEST 3: ARMED -> DISARMING -> DISARMED
// ============================================================================
TEST_F(FiringFSMTest, DisarmFromArmed) {
  armFSM();
  ASSERT_EQ(fsm->getCurrentState(), FiringState::ARMED);

  resetCounters();
  fsm->triggerDisarming();
  runCycle();    // -> DISARMING
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMING);
  EXPECT_FALSE(fsm->isArmed());

  runCycle();    // -> DISARMED
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMED);
  EXPECT_EQ(detachESCsCalls, 1);
  EXPECT_EQ(detachShotCalls, 1);
}

// ============================================================================
// TEST 4: Volle Schusssequenz
// ARMED -> SPINNING_UP -> PUSHING -> BRAKING -> COOLDOWN -> ARMED
// ============================================================================
TEST_F(FiringFSMTest, FullFireSequence) {
  armFSM();
  resetCounters();

  // Schuss auslösen mit 60% Leistung
  fsm->triggerFire(60);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::SPINNING_UP);
  EXPECT_EQ(lastFlywheelPower, 60);

  // SPINUP_MS warten -> PUSHING
  advanceMillis(Config::SPINUP_MS);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::PUSHING);
  EXPECT_EQ(attachShotCalls, 1);
  // Servo-Position: neutral + SHOT_SPEED_OFFSET
  EXPECT_EQ(lastShotServoUs, (int)(Config::SHOT_NEUTRAL_DEFAULT + Config::SHOT_SPEED_OFFSET));

  // SHOT_DURATION_DEFAULT warten -> BRAKING
  advanceMillis(Config::SHOT_DURATION_DEFAULT);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::BRAKING);
  // Servo-Position: neutral - BRAKE_OFFSET
  EXPECT_EQ(lastShotServoUs, (int)(Config::SHOT_NEUTRAL_DEFAULT - Config::BRAKE_OFFSET));

  // BRAKE_MS warten -> COOLDOWN
  advanceMillis(Config::BRAKE_MS);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::COOLDOWN);
  EXPECT_EQ(lastFlywheelPower, 0);    // Motoren aus
  // Servo-Position: neutral
  EXPECT_EQ(lastShotServoUs, (int)Config::SHOT_NEUTRAL_DEFAULT);

  // 100ms warten -> ARMED
  advanceMillis(100);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMED);
  EXPECT_TRUE(fsm->isArmed());
}

// ============================================================================
// TEST 5: ESC_TEST
// ============================================================================
TEST_F(FiringFSMTest, EscTest_ArmedToEscTestToDisarming) {
  armFSM();
  resetCounters();

  fsm->triggerEscTest(30);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ESC_TEST);
  EXPECT_EQ(lastFlywheelPower, 30);

  // Disarm beendet den Test
  fsm->triggerDisarming();
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMING);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMED);
}

// ============================================================================
// TEST 6: CALIBRATING -> IDLE (Sonderfall von triggerDisarming)
// ============================================================================
TEST_F(FiringFSMTest, Calibration_ArmedToCalibratingToIdle) {
  armFSM();
  resetCounters();

  fsm->triggerCalibration();
  // triggerCalibration setzt _currentState und _nextState direkt
  EXPECT_EQ(fsm->getCurrentState(), FiringState::CALIBRATING);
  EXPECT_GE(attachESCsCalls, 1);    // ESCs werden angehängt

  // Disarm im CALIBRATING-Modus -> Sonderfall: geht direkt zu IDLE
  fsm->triggerDisarming();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::IDLE);
}

// ============================================================================
// TEST 7: Auto-Disarm nach 60s Inaktivität
// ============================================================================
TEST_F(FiringFSMTest, AutoDisarm_AfterTimeout) {
  armFSM();
  ASSERT_TRUE(fsm->isArmed());
  ASSERT_EQ(fsm->getCurrentState(), FiringState::ARMED);

  // 60 Sekunden + 1ms vergehen ohne Activity
  advanceMillis(Config::AUTO_DISARM_MS + 1);
  runCycle();    // evalTransition erkennt Timeout -> DISARMING
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMING);
  EXPECT_FALSE(fsm->isArmed());

  runCycle();    // -> DISARMED
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMED);
}

// ============================================================================
// TEST 8: Re-Arm nach DISARMED
// ============================================================================
TEST_F(FiringFSMTest, ReArm_FromDisarmed) {
  armFSM();
  fsm->triggerDisarming();
  runCycle();    // DISARMING
  runCycle();    // DISARMED
  ASSERT_EQ(fsm->getCurrentState(), FiringState::DISARMED);

  // Erneut ARM
  fsm->triggerArming();
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMING);

  advanceMillis(Config::ARM_DELAY_MS);
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMED);
  EXPECT_TRUE(fsm->isArmed());
}

// ============================================================================
// TEST 9: Guard - triggerFire ohne ARM
// ============================================================================
TEST_F(FiringFSMTest, FireGuard_NotArmed) {
  ASSERT_EQ(fsm->getCurrentState(), FiringState::IDLE);

  fsm->triggerFire(50);
  runCycle();
  // Muss in IDLE bleiben
  EXPECT_EQ(fsm->getCurrentState(), FiringState::IDLE);
  EXPECT_FALSE(fsm->isArmed());
}

// ============================================================================
// TEST 10: Guard - triggerArming wenn bereits ARMED
// ============================================================================
TEST_F(FiringFSMTest, ArmGuard_AlreadyArmed) {
  armFSM();
  ASSERT_EQ(fsm->getCurrentState(), FiringState::ARMED);

  // Nochmal ARM senden - sollte nichts tun
  fsm->triggerArming();
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMED);
  EXPECT_TRUE(fsm->isArmed());
}

// ============================================================================
// TEST 11: Disarm während Schusssequenz (SPINNING_UP)
// ============================================================================
TEST_F(FiringFSMTest, DisarmDuringFire) {
  armFSM();
  fsm->triggerFire(50);
  runCycle();
  ASSERT_EQ(fsm->getCurrentState(), FiringState::SPINNING_UP);

  // Notfall-Disarm
  fsm->triggerDisarming();
  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMING);

  runCycle();
  EXPECT_EQ(fsm->getCurrentState(), FiringState::DISARMED);
}

// ============================================================================
// TEST 12: Cooldown endet in ARMED (nicht IDLE)
// ============================================================================
TEST_F(FiringFSMTest, CooldownReturnsToArmed) {
  armFSM();
  fsm->triggerFire(40);
  runCycle();    // SPINNING_UP
  advanceMillis(Config::SPINUP_MS);
  runCycle();    // PUSHING
  advanceMillis(Config::SHOT_DURATION_DEFAULT);
  runCycle();    // BRAKING
  advanceMillis(Config::BRAKE_MS);
  runCycle();    // COOLDOWN
  advanceMillis(100);
  runCycle();    // -> ARMED (nicht IDLE!)

  EXPECT_EQ(fsm->getCurrentState(), FiringState::ARMED);
  EXPECT_TRUE(fsm->isArmed());
  EXPECT_TRUE(fsm->canFire());    // Sofort wieder schussbereit
}

// ============================================================================
// TEST 13: Callback-Verifizierung (Entry Actions)
// ============================================================================
TEST_F(FiringFSMTest, CallbacksVerification) {
  // ARMING -> attachESCs aufgerufen
  fsm->triggerArming();
  runCycle();
  EXPECT_EQ(attachESCsCalls, 1);
  EXPECT_EQ(detachESCsCalls, 0);

  // ARMED -> kein Servo/ESC Callback
  int prevAttach = attachESCsCalls;
  advanceMillis(Config::ARM_DELAY_MS);
  runCycle();
  EXPECT_EQ(attachESCsCalls, prevAttach);    // Nicht nochmal attach

  // DISARMING -> isArmed wird false
  fsm->triggerDisarming();
  runCycle();
  EXPECT_FALSE(fsm->isArmed());

  // DISARMED -> detachESCs + detachShot
  resetCounters();
  runCycle();
  EXPECT_EQ(detachESCsCalls, 1);
  EXPECT_EQ(detachShotCalls, 1);
}

// === GoogleTest Entry Point ===
int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
