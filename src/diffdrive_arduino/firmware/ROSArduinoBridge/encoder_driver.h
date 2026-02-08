/* *************************************************************
   Encoder driver function definitions - by James Nugen
   Extended for Pi Pico support
   ************************************************************ */

#ifndef ENCODER_DRIVER_H
#define ENCODER_DRIVER_H

// Include centralized pin definitions for Raspberry Pi Pico
#include "pinout.h"
   
#ifdef ARDUINO_ENC_COUNTER
  //below can be changed, but should be PORTD pins; 
  //otherwise additional changes in the code are required

  // ============== ARDUINO AVR (Nano, Uno, Mega) ==============
  #if defined(__AVR__)
    // AVR uses specific port pins for efficient interrupt handling
    // These should be PORTD pins for left encoder
    #define LEFT_ENC_PIN_A PD2  //pin 2
    #define LEFT_ENC_PIN_B PD3  //pin 3
    //below can be changed, but should be PORTC pins
    // These should be PORTC pins for right encoder
    #define RIGHT_ENC_PIN_A PC4  //pin A4
    #define RIGHT_ENC_PIN_B PC5   //pin A5
    
  // ============== RASPBERRY PI PICO (RP2040) ==============
  #elif defined(ARDUINO_ARCH_RP2040)
    // Pin definitions are now in pinout.h for centralized management
    // See pinout.h for complete pin allocation table
    // Encoder pins are already defined in pinout.h
    
  #else
    #error "Unsupported platform! Use Arduino AVR or Raspberry Pi Pico"
  #endif

#endif
   
long readEncoder(int i);
void resetEncoder(int i);
void resetEncoders();

#endif // ENCODER_DRIVER_H

