/* CONSTRUCT LASER TRIPWIRE CODE
 *  WRITTEN BY Z. COOK
 *  
 *  
 *  ---------------------------------------
 *  Pinout:
 *  7: Seven segment display strobe
 *  8: Seven segment display data
 *  9: Seven segment display clock
 *  10: Laser diode
 *  A0: Photoresistor sensor
 */

// Load library for TMC1638 8 x Seven Segment Display ith Keys and LEDs display
#include <TM1638.h>

// CONFIG
// Pins
const int displayStrobePin = 7;
const int displayDataPin = 8;
const int displayClockPin = 9;
const int laserPin = 10;
const int photoresistorPin = A0;

// If 0, the laser will be disabled when the Arduino initializes
const int laserEnabledOnStart = 1;
// Threshold of photoresistor to be tripped from 0 to 1000
const int photoresistorThreshold = 100;

// LED that turns on when laser is tripped. Set to 0 to disable
const byte trippedLEDDebug = 64;

// Name of the board to send over serial.
String boardName = "Main Lab Front Door Laser";






// VARIABLES
// Button currently down
byte buttonCurrentlyDown = 0;
// Number displayed on screen
double numberToDisplay = 0;
// Count of people who passed through door
unsigned long doorPassCounter = 0;
// 1 is laser is enabled or 0 if laser is disabled
int laserEnabled = laserEnabledOnStart;
// Last time trip wire was triggered
unsigned long lastTripwireTime = 0;
// Offset to add to LEDs. USed with trippedLEDDebug
byte buttonLEDOnOffset = 0;
// Button statuses
byte buttonDownIndividualStatuses[] = {0,0,0,0,0,0,0,0};
// Determines the state of the display.
int showSensetivity = 0; 

// Define module for seven segment display TMC1638
TM1638 module(displayDataPin,displayClockPin,displayStrobePin);





// CUSTOM FUNCTIONS
/*
 * Update display to number of people
 */
void updateDisplayToPeopleCounter() {
  // Update display
  numberToDisplay = 0;
  if (showSensetivity == 0) {
    numberToDisplay = floor(doorPassCounter/2.0);
  } else if (showSensetivity == 1) {
    numberToDisplay = floor(analogRead(photoresistorPin));
  }
  module.setDisplayToDecNumber(numberToDisplay,0x00);

  // Print serial to update clock
  Serial.println(numberToDisplay);
}

/*
 * Invoked when laser has been tripped and how long it has been broken
 * Will not be called when laser is disabled
 * Should be edited based on setup. Default is optimized for ankle level.
 */
void laserTripped(unsigned long timeDownMillis) {
  // Increment counter
  doorPassCounter = doorPassCounter += 1;

  // Update display
  updateDisplayToPeopleCounter();

  // Output string PASS if number of people changed
  if (doorPassCounter % 2 == 0) {
    Serial.println("INCREMENT");
  }
}

/*
 * Invoked when a button is pressed and released, with the button number
 */
void buttonPressed(byte buttonId) {
  if (buttonId == 1) {
    // 1st button pressed: Increase counter by 2
    doorPassCounter = doorPassCounter + 2;
    updateDisplayToPeopleCounter();
    Serial.println("MANUALADD");
  } else if (buttonId == 2) {
    // 2nd button pressed: Decrease counter by 2
    doorPassCounter = doorPassCounter - 2;
    if (doorPassCounter < 0 || doorPassCounter > ceil(pow(10,8)) - 1) {
      doorPassCounter = 0;
    }
    Serial.println("MANUALSUB");
    updateDisplayToPeopleCounter();
  } else if (buttonId == 4) {
    // 3rd button pressed: Enable/disable laser
    if (laserEnabled == 1) {
      laserEnabled = 0;
    } else {
      laserEnabled = 1;
    }
  } else if (buttonId == 8) {
    // 4th button pressed: Send refresh signal
    Serial.println("REFRESH");
  } else if (buttonId == 16) {
    // 5th button pressed: Nothing
  } else if (buttonId == 32) {
    // 6th button pressed: Change the debug button.
    if (showSensetivity == 0) {
      showSensetivity = 1;
    } else {
      showSensetivity = 0;
    }
    updateDisplayToPeopleCounter();
  } else if (buttonId == 64) {
    // 7th button pressed: Reserved
  } else if (buttonId == 128) {
    // 8th button pressed: Reset counter
    doorPassCounter = 0;
    Serial.println("CLEAR");
    updateDisplayToPeopleCounter();
  }
}

/*
 * Invoked when a Serial message is input.
 * 
 * Current commands:
 *    SET:NNNNNNNN   - Sets number to display
 *    GETNAME        - Serial prints NAME:boardName
 */
void serialInput(String input) {
  // If command is "SET:_______", change door passes
  // IF command is "GETNAME", print NAME:boardName
  if (input.substring(0,4).equals("SET:")) {
    // Move string to buffer
    char inputLongBuffer[9];
    input.substring(4).toCharArray(inputLongBuffer,sizeof(inputLongBuffer));
    // Set door passes
    long inputLong = atol(inputLongBuffer);
    doorPassCounter = inputLong * 2;
    updateDisplayToPeopleCounter();
  } else if (input.substring(0,8).equals("GETNAME")) {
    Serial.println("NAME:" + boardName);
  }
}





// MAIN FUNCTIONS
/*
 * Update which button is down, if any
 */
void updateButtonsPressed() {
  // Update buttons pressed and update LEDs above
  buttonCurrentlyDown = module.getButtons() + buttonLEDOnOffset;
  module.setLEDs(buttonCurrentlyDown & 0xFF);
}

/*
 * Determines what buttons are pressed
 */
void signalButtonsToPress() {
  byte currentButtonsDown = buttonCurrentlyDown;

  // Go through buttons and signal ones down
  for (int i = 7; i >= 0; i--) {
    int buttonId = floor(pow(2,i) + 0.5);
    byte currentButtonState = buttonDownIndividualStatuses[i];
    byte newTotalState = currentButtonsDown % buttonId;

    // Change state if needed
    if (newTotalState == currentButtonsDown) {
      buttonDownIndividualStatuses[i] = 0;
    } else {
      currentButtonsDown = newTotalState;
      buttonDownIndividualStatuses[i] = 1;
    }

    // Update button down if went from down to up
    if (currentButtonState == 0 && buttonDownIndividualStatuses[i] == 1) {
      buttonPressed(buttonId);
    }
  }
}

/*
 * Function invoked every cycle step
 */
void laserCycleStep() {
  // Update buttons
  byte previousButtonDown = buttonCurrentlyDown;
  updateButtonsPressed();

  // If the sensetivity is being shown, display the sensitivity.
  if (showSensetivity == 1) {
    updateDisplayToPeopleCounter();
    delay(100);
  }
  
  // If buttons changed, call update function
  if (buttonCurrentlyDown != previousButtonDown) {
    signalButtonsToPress();
  }
  
  // If the laser is enabled, run the tripwire
  if (laserEnabled == 1) {
    int resistorValue = analogRead(photoresistorPin);

    // Set LED offset
    if (resistorValue < photoresistorThreshold) {
      buttonLEDOnOffset = trippedLEDDebug;
    } else {
      buttonLEDOnOffset = 0;
    }
    
    if (lastTripwireTime == 0 && resistorValue < photoresistorThreshold) {
      // If laser was tripped, set time to current time
      lastTripwireTime = millis();
    } else if (lastTripwireTime != 0 && resistorValue > photoresistorThreshold) {
      // If laser is no longer tripped and counter was set, invoke laserTripped and set timer to 0
      laserTripped(millis() - lastTripwireTime);
      lastTripwireTime = 0;
    }
  } else {
    // Reset tripwire state
    lastTripwireTime = 0;
  }
  
  // Enable/disable laser
  if (laserEnabled == 1) {
    digitalWrite(laserPin,HIGH);
  } else {
    digitalWrite(laserPin,LOW);
  }

  // Update serial input
  while (Serial.available()) {
    serialInput(Serial.readString());
  }
}

 
/*
 * Main setup function when intitialized
 */
void setup() {
  // Set up pins
  Serial.begin(9600);
  pinMode(laserPin,OUTPUT);

  // Set up display
  module.clearDisplay();
  updateDisplayToPeopleCounter();

  // Output startup message
  Serial.println("STARTUP:" + boardName);
}



/*
 * Main loop function after initialized
 */
void loop() {
  laserCycleStep();
}
