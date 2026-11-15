#include <TinyWireS.h>

#define I2C_ADDRESS 0x08
// Dynamically calculate clock based on IDE settings (Prescaler 8)
#define TIMER_CLOCK (F_CPU / 8UL)

volatile uint16_t lastCapture = 0;
volatile uint16_t periodTicks = 0;
volatile uint16_t lastFreq = 0;
volatile bool newPeriod = false;

void setup() {
  TinyWireS.begin(I2C_ADDRESS);
  TinyWireS.onRequest(requestEvent);

  // PA1 is Physical Leg 12 / Arduino Pin 1
  pinMode(1, OUTPUT); 
  digitalWrite(1, HIGH);

  // PA7 is Physical Leg 6 / Arduino Pin 7 (ICP1)
  pinMode(7, INPUT); 

  // Timer1 Setup for Input Capture
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;

  TCCR1B |= (1 << ICES1);   // Capture on Rising Edge
  TCCR1B |= (1 << CS11);    // Prescaler = 8
  TIMSK1 |= (1 << ICIE1);   // Enable Input Capture Interrupt
}

void loop() {
  if (newPeriod) {
    uint16_t localTicks;

    // Atomic copy of periodTicks to prevent corruption during ISR
    cli();
    localTicks = periodTicks;
    newPeriod = false;
    sei();

    if (localTicks > 10) { // Filter out impossible/noisy high frequencies
      lastFreq = (uint16_t)(TIMER_CLOCK / localTicks);
    } else {
      lastFreq = 0;
    }
  }

  // Required for TinyWireS to handle the I2C state machine
  TinyWireS_stop_check();
}

ISR(TIMER1_CAPT_vect) {
  uint16_t capture = ICR1;
  
  // Standard 16-bit subtraction handles the wrap-around (overflow) automatically
  periodTicks = capture - lastCapture;
  lastCapture = capture;
  newPeriod = true;
}

// I2C request handler - This runs when the Master (Uno) asks for data
void requestEvent() {
  // ATtiny84A TinyWireS uses .write()
  TinyWireS.write((uint8_t)(lastFreq >> 8));   // Send High Byte
  TinyWireS.write((uint8_t)(lastFreq & 0xFF)); // Send Low Byte
}