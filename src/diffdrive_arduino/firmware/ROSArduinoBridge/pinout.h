/***************************************************************
   Raspberry Pi Pico Pin Configuration
   
   Centralized pin definitions for all peripherals
   
   Raspberry Pi Pico RP2040 has:
   - 26 GPIO pins (GP0-GP28, excluding GP23-25 which are used internally)
   - 8 PWM Slices (0-7), each with 2 channels (A/B)
   - 2 UART, 2 SPI, 2 I2C interfaces
   - 3 ADC channels (GP26, GP27, GP28)
   
   PWM Slice Mapping:
   PWM0: GP0(A), GP1(B), GP16(A), GP17(B)
   PWM1: GP2(A), GP3(B), GP18(A), GP19(B)
   PWM2: GP4(A), GP5(B), GP20(A), GP21(B)
   PWM3: GP6(A), GP7(B), GP22(A), (GP23-internal)
   PWM4: GP8(A), GP9(B), GP24(A), (GP25-LED)
   PWM5: GP10(A), GP11(B), GP26(A), GP27(B)
   PWM6: GP12(A), GP13(B), GP28(A)
   PWM7: GP14(A), GP15(B)
   
   *************************************************************/

#ifndef PINOUT_H
#define PINOUT_H

// Only compile for Raspberry Pi Pico
#if defined(ARDUINO_ARCH_RP2040)

// ============================================================
// MOTOR DRIVER PINS (TB6612FNG)
// ============================================================
// Motor A (Left Motor)
// Note: PWM pin must be on different slice than direction pins
// to avoid PWM conflicts when using digitalWrite()
#define LEFT_MOTOR_PWM    0    // GP0  - PWM0A
#define LEFT_MOTOR_IN1    4    // GP4  - PWM2A (used as digital output)
#define LEFT_MOTOR_IN2    5    // GP5  - PWM2B (used as digital output)

// Motor B (Right Motor)
#define RIGHT_MOTOR_PWM   6    // GP6  - PWM3A
#define RIGHT_MOTOR_IN1   7    // GP7  - PWM3B (used as digital output)
#define RIGHT_MOTOR_IN2   8    // GP8  - PWM4A (used as digital output)

// TB6612 STBY (Standby) Pin
// Connect STBY to 3.3V (always enabled) or control via GPIO
// #define MOTOR_STBY     XX   // Optional: GPIO for standby control

// ============================================================
// ENCODER PINS (Quadrature Encoders)
// ============================================================
// Left Encoder
#define LEFT_ENC_PIN_A    22   // GP22 - PWM3A
#define LEFT_ENC_PIN_B    21   // GP21 - PWM2B

// Right Encoder  
#define RIGHT_ENC_PIN_A   11   // GP11 - PWM5B
#define RIGHT_ENC_PIN_B   10   // GP10 - PWM5A

// ============================================================
// SPI0 INTERFACE (IMU Sensor - ICM-20948)
// ============================================================
// 9-DOF IMU: 3-Axis Accelerometer, Gyroscope, Magnetometer
#define SPI0_MISO         16   // GP16 - PWM0A
#define SPI0_CS           17   // GP17 - PWM0B (Chip Select)
#define SPI0_SCK          18   // GP18 - PWM1A (Clock)
#define SPI0_MOSI         19   // GP19 - PWM1B

// Alternative: Use GP17 as CS or any free GPIO
#define IMU_CS            SPI0_CS

// ============================================================
// I2C0 INTERFACE (Optional sensors)
// ============================================================
// Default I2C0 pins (can be changed if needed)
#define I2C0_SDA          12   // GP12 - PWM6A
#define I2C0_SCL          13   // GP13 - PWM6B

// ============================================================
// I2C1 INTERFACE (Optional sensors)
// ============================================================
// Default I2C1 pins (alternative location)
#define I2C1_SDA          14   // GP14 - PWM7A
#define I2C1_SCL          15   // GP15 - PWM7B

// ============================================================
// UART0 (USB Serial via USB)
// ============================================================
// GP0 (TX) and GP1 (RX) are default UART0
// But we're using USB serial, so these are available
// Already using GP0 for LEFT_MOTOR_PWM

// ============================================================
// UART1 (Hardware Serial - Optional GPS, etc.)
// ============================================================
#define UART1_TX          20   // GP20 - PWM2A (used as UART)
// #define UART1_RX       21   // GP21 - Already used by LEFT_ENC_PIN_B

// ============================================================
// ANALOG INPUT PINS (ADC)
// ============================================================
#define ADC0_PIN          26   // GP26 - ADC0, PWM5A
#define ADC1_PIN          27   // GP27 - ADC1, PWM5B
#define ADC2_PIN          28   // GP28 - ADC2, PWM6A

// ============================================================
// DIGITAL I/O PINS (Available/Spare)
// ============================================================
#define GPIO_SPARE_1      1    // GP1  - PWM0B
#define GPIO_SPARE_2      2    // GP2  - PWM1A
#define GPIO_SPARE_3      3    // GP3  - PWM1B
#define GPIO_SPARE_4      9    // GP9  - PWM4B

// GP15 might be available if not using I2C1
// #define GPIO_SPARE_5   15   // GP15 - PWM7B

// ============================================================
// ONBOARD LED
// ============================================================
#define LED_BUILTIN       25   // GP25 - Onboard LED (PWM4B)

// ============================================================
// RESERVED/INTERNAL PINS (Do not use)
// ============================================================
// GP23 - SMPS power save pin (internal)
// GP24 - VBUS sense (internal)
// GP29 - ADC3 for VSYS voltage measurement

// ============================================================
// PIN SUMMARY & ALLOCATION TABLE
// ============================================================
/*
    PIN ALLOCATION MAP:
    
    GP0  - LEFT_MOTOR_PWM      (Motor Control)
    GP1  - SPARE               (Available)
    GP2  - SPARE               (Available)
    GP3  - SPARE               (Available)
    GP4  - LEFT_MOTOR_IN1      (Motor Control)
    GP5  - LEFT_MOTOR_IN2      (Motor Control)
    GP6  - RIGHT_MOTOR_PWM     (Motor Control)
    GP7  - RIGHT_MOTOR_IN1     (Motor Control)
    GP8  - RIGHT_MOTOR_IN2     (Motor Control)
    GP9  - SPARE               (Available)
    GP10 - RIGHT_ENC_PIN_B     (Encoder)
    GP11 - RIGHT_ENC_PIN_A     (Encoder)
    GP12 - I2C0_SDA            (I2C - Optional)
    GP13 - I2C0_SCL            (I2C - Optional)
    GP14 - I2C1_SDA            (I2C - Optional)
    GP15 - I2C1_SCL            (I2C - Optional)
    GP16 - SPI0_MISO           (IMU Sensor)
    GP17 - SPI0_CS             (IMU Sensor)
    GP18 - SPI0_SCK            (IMU Sensor)
    GP19 - SPI0_MOSI           (IMU Sensor)
    GP20 - UART1_TX            (Serial - Optional)
    GP21 - LEFT_ENC_PIN_B      (Encoder)
    GP22 - LEFT_ENC_PIN_A      (Encoder)
    GP23 - INTERNAL            (Do not use)
    GP24 - INTERNAL            (Do not use)
    GP25 - LED_BUILTIN         (Onboard LED)
    GP26 - ADC0                (Analog Input - Available)
    GP27 - ADC1                (Analog Input - Available)
    GP28 - ADC2                (Analog Input - Available)
    GP29 - ADC3/VSYS           (Internal voltage sense)
*/

#endif // ARDUINO_ARCH_RP2040

#endif // PINOUT_H
