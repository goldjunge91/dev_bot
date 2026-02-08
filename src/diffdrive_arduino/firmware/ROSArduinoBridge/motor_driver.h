/***************************************************************
   Motor driver function definitions - by James Nugen
   Extended for Pi Pico support
   *************************************************************/

#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

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
    // Motor A (Left Motor)
    #define LEFT_MOTOR_PWM    2   // GP2 - PWM1A
    #define LEFT_MOTOR_IN1    3   // GP3 - PWM1B (WARNING: shares PWM slice with GP2!)
    #define LEFT_MOTOR_IN2    4   // GP4 - PWM2A
    
    // Motor B (Right Motor)  
    #define RIGHT_MOTOR_PWM   6   // GP6 - PWM3A
    #define RIGHT_MOTOR_IN1   7   // GP7 - PWM3B
    #define RIGHT_MOTOR_IN2   8   // GP8 - PWM4A
  #endif
  
  // STBY should be connected to 3.3V (Pico) or 5V (Nano)
#endif

void initMotorController();
void setMotorSpeed(int i, int spd);
void setMotorSpeeds(int leftSpeed, int rightSpeed);

#endif // MOTOR_DRIVER_H
