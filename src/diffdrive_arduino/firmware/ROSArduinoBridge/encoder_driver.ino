/* *************************************************************
   Encoder definitions
   
   Add an "#ifdef" block to this file to include support for
   a particular encoder board or library. Then add the appropriate
   #define near the top of the main ROSArduinoBridge.ino file.
   
   Extended for Pi Pico (RP2040) support
   ************************************************************ */
   
#ifdef USE_BASE

#ifdef ROBOGAIA
  /* The Robogaia Mega Encoder shield */
  #include "MegaEncoderCounter.h"

  /* Create the encoder shield object */
  MegaEncoderCounter encoders = MegaEncoderCounter(4); // Initializes the Mega Encoder Counter in the 4X Count mode
  
  /* Wrap the encoder reading function */
  long readEncoder(int i) {
    if (i == LEFT) return encoders.YAxisGetCount();
    else return encoders.XAxisGetCount();
  }

  /* Wrap the encoder reset function */
  void resetEncoder(int i) {
    if (i == LEFT) return encoders.YAxisReset();
    else return encoders.XAxisReset();
  }

#elif defined(ARDUINO_ENC_COUNTER)

  volatile long left_enc_pos = 0L;
  volatile long right_enc_pos = 0L;
  
  // ============== ARDUINO AVR (Nano, Uno, Mega) ==============
  #if defined(__AVR__)
    static const int8_t ENC_STATES [] = {0,1,-1,0,-1,0,0,1,1,0,0,-1,0,-1,1,0};  //encoder lookup table

      
     /* Interrupt routine for LEFT encoder, taking care of actual counting */
    ISR (PCINT2_vect){
      static uint8_t enc_last=0;
      enc_last <<=2; //shift previous state two places
      enc_last |= (PIND & (3 << 2)) >> 2; //read the current state into lowest 2 bits
      left_enc_pos += ENC_STATES[(enc_last & 0x0f)];
    }
    
     /* Interrupt routine for RIGHT encoder, taking care of actual counting */
    ISR (PCINT1_vect){
      static uint8_t enc_last=0;
      /* Wrap the encoder reading function */
      enc_last <<=2; //shift previous state two places
	enc_last |= (PINC & (3 << 4)) >> 4; //read the current state into lowest 2 bits
  
      right_enc_pos += ENC_STATES[(enc_last & 0x0f)];
    }
    
     /* Wrap the encoder reading function */
    void initEncoders() {
      // Encoder pins are set up in main setup() for AVR
    }
  
  // ============== RASPBERRY PI PICO (RP2040) ==============
  #elif defined(ARDUINO_ARCH_RP2040)
  
    // Store last state for quadrature decoding
    volatile uint8_t left_enc_last = 0;
    volatile uint8_t right_enc_last = 0;
    
    /* Interrupt handler for LEFT encoder */
    void leftEncoderISR() {
      uint8_t state = (digitalRead(LEFT_ENC_PIN_A) << 1) | digitalRead(LEFT_ENC_PIN_B);
      uint8_t combined = (left_enc_last << 2) | state;
      
      // Quadrature state machine
      switch(combined) {
        case 0b0001: case 0b0111: case 0b1110: case 0b1000:
          left_enc_pos++;
          break;
        case 0b0010: case 0b1011: case 0b1101: case 0b0100:
          left_enc_pos--;
          break;
      }
      left_enc_last = state;
    }
    
    /* Interrupt handler for RIGHT encoder */
    void rightEncoderISR() {
      uint8_t state = (digitalRead(RIGHT_ENC_PIN_A) << 1) | digitalRead(RIGHT_ENC_PIN_B);
      uint8_t combined = (right_enc_last << 2) | state;
      
      // Quadrature state machine
      switch(combined) {
        case 0b0001: case 0b0111: case 0b1110: case 0b1000:
          right_enc_pos++;
          break;
        case 0b0010: case 0b1011: case 0b1101: case 0b0100:
          right_enc_pos--;
          break;
      }
      right_enc_last = state;
    }
    
    void initEncoders() {
      // Set encoder pins as inputs with pullups
      pinMode(LEFT_ENC_PIN_A, INPUT_PULLUP);
      pinMode(LEFT_ENC_PIN_B, INPUT_PULLUP);
      pinMode(RIGHT_ENC_PIN_A, INPUT_PULLUP);
      pinMode(RIGHT_ENC_PIN_B, INPUT_PULLUP);
      
      // Read initial states
      left_enc_last = (digitalRead(LEFT_ENC_PIN_A) << 1) | digitalRead(LEFT_ENC_PIN_B);
      right_enc_last = (digitalRead(RIGHT_ENC_PIN_A) << 1) | digitalRead(RIGHT_ENC_PIN_B);
      
      // Attach interrupts to all encoder pins (Pi Pico supports this!)
      attachInterrupt(digitalPinToInterrupt(LEFT_ENC_PIN_A), leftEncoderISR, CHANGE);
      attachInterrupt(digitalPinToInterrupt(LEFT_ENC_PIN_B), leftEncoderISR, CHANGE);
      attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_PIN_A), rightEncoderISR, CHANGE);
      attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_PIN_B), rightEncoderISR, CHANGE);
    }
    
  #endif  // Platform selection

  /* Read encoder value - works on all platforms */
  long readEncoder(int i) {
    if (i == LEFT) return left_enc_pos;
    else return right_enc_pos;
  }

   /* Wrap the encoder reset function  Reset single encoder - works on all platforms */
  void resetEncoder(int i) {
    if (i == LEFT){
      left_enc_pos=0L;
      return;
    } else { 
      right_enc_pos=0L;
      return;
    }
  }

#else
  #error A encoder driver must be selected!
#endif

/* Wrap the encoder reset function Reset all encoders - works on all platforms */
void resetEncoders() {
  resetEncoder(LEFT);
  resetEncoder(RIGHT);
}

#endif

