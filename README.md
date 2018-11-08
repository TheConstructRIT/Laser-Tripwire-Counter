# Laser-Tripewire-Counter
The laser trwipwire counter system is a custom system to
give an idea of how many people come into the main lab.

# LaserTripWireBackEnd
The back end to handle persistence is written in Python
and utilizes the serial input/output over USB. It is 
intended to be run on startup with Windows. When the 
Arduino is connected, it will send the last count. It will
also recieve increment/decrement signals to store.

## Protocol for Signals
The following commands are used for sending signals from the Arduino:
* STARTUP:counterName - Signal that the Arduino has started up and sends the current count.
	* counterName - The name assigned to the Arduino.
* NAME:counterName - Resets the internal state and sends the current count.
	* counterName - The name assigned to the Arduino.
* INCREMENT - Increments the counter by 1.
* MANUALADD - Increments the counter by 1. This is used instead of INCREMENT if it was added manually.
* MANUALSUB - Decrements the counter by 1.
* CLEAR - Clears the counter.
* REFRESH - Requests to send the latest count.

The following commands are used for sending signals to the Arduino:
* GETNAME - Requests the name from the Arduino.
* SET:count - Sets the count of the counter.
	* count - The current count.

# Configuration
The following configuration options are avaliable in the given files:
* SerialReaderWriter.pyw
	* `MAX_SERIAL_TO_CHECK` - The maximum COM port to check as [1,MAX_SERIAL_TO_CHECK].
	* `COM_REFRESH_TIME` - The time between checking the COM ports in seconds.
	* `COUNTER_STATE_FILE_NAME_END` - The file name ending used for persistence.
* DataCollection.py
	* `TIMESTAMP_DATA_FILE_NAME_END` - The file name ending used for the timestamps.
* LaserCounterCircuit.ino
	* 5x configurable pins (see below)
	* `laserEnabledOnStart` - Determines if the laser is on when initialized.
	* `photoresistorThreshold` - The threshold between the laser being detected and not detected.
	* `trippedLEDDebug` - The LED to use for debugging the laser being tripped on the TM1638 board.
	* `boardName` - The name assigned for the laser.

# Arduino Circuit
The hardware required for the system includes:
* An Arduino
* A photoresistor
* A lasre diode
* A TM1638 seven segment display and buttons

The pinout on the Arudino includes:
* Pin 7 - TM1638 Strobe (STB)
	* Configurable with `displayStrobePin`
* Pin 8 - TM1638 Data (DIO)
	* Configurable with `displayDataPin`
* Pin 9 - TM1638 Clock (CLK)
	* Configurable with `displayClockPin`
* Pin 10 - Laser diode power
	* Configurable with `laserPin`
* Pin A0 - Photoresistor
	* Configurable with `photoresistorPin`