/***************************************************************
   Motor driver function definitions - by James Nugen
   Extended for Pi Pico support
   *************************************************************/

#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

// Include centralized pin definitions for Raspberry Pi Pico
#include "pinout.h"

#ifdef L298_MOTOR_DRIVER
  #define RIGHT_MOTOR_BACKWARD 5
  #define LEFT_MOTOR_BACKWARD  6
  #define RIGHT_MOTOR_FORWARD  9
  #define LEFT_MOTOR_FORWARD   10
  #define RIGHT_MOTOR_ENABLE 12
  #define LEFT_MOTOR_ENABLE 13
#endif

#ifdef TB6612_MOTOR_DRIVER

  // ============== ARDUINO AVR (Nano, Uno, Mega) ==============
  #if defined(__AVR__)
    // Motor A (Left Motor)
    #define LEFT_MOTOR_PWM    3   // PWMA - PWM pin
    #define LEFT_MOTOR_IN1    4   // AIN1 - Direction
    #define LEFT_MOTOR_IN2    5   // AIN2 - Direction
    
    // Motor B (Right Motor)  
    #define RIGHT_MOTOR_PWM   9   // PWMB - PWM pin
    #define RIGHT_MOTOR_IN1   7   // BIN1 - Direction
    #define RIGHT_MOTOR_IN2   8   // BIN2 - Direction

  // ============== RASPBERRY PI PICO (RP2040) ==============
  #elif defined(ARDUINO_ARCH_RP2040)
    // Pin definitions are now in pinout.h for centralized management
    // See pinout.h for complete pin allocation table
    // Motor pins are already defined in pinout.h
  #endif
  
  // STBY should be connected to 3.3V (Pico) or 5V (Nano)
#endif

void initMotorController();
void setMotorSpeed(int i, int spd);
void setMotorSpeeds(int leftSpeed, int rightSpeed);

#endif // MOTOR_DRIVER_H
