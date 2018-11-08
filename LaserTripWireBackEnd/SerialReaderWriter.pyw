"""
Construct laser trip wire back end code

Author: Z. Cook
"""

import serial
import threading
import os
from time import sleep
import DataCollection

# Max serial inputs to check
MAX_SERIAL_TO_CHECK = 20
# How many seconds to refresh the connected COMs in seconds
COM_REFRESH_TIME = 2
# End of file name to store last state
COUNTER_STATE_FILE_NAME_END = "_SerialCounterLastNumber.txt"





"""
Checks if a file exists. If it doesn't, creates the file with the text "0"
"""
def createFileIfNone(fileName):
    # Check if the file exists
    if not os.path.exists(fileName):
        # Write a new file
        file = open(fileName,"w+")
        file.write("0")
        file.close()

"""
Gets the current state in the file. If it isn't a number, it will override the file to 0.
"""
def getCurrentCounterState(fileName):
    # Create the file if it doesn't exist
    createFileIfNone(fileName)

    # Read the file
    file = open(fileName,"r+")
    line = file.readline()

    # Override the file if it is corrupt
    if not line.isdigit():
        file.seek(0)
        file.write("0")
        file.truncate(1)
        line = "0"

    # Close the file
    file.close()

    # Return the first line as a string
    return line

"""
Set the state of the given file.
"""
def setCurrentCounterState(fileName,newNumber):
    # Create the file if it doesn't exist
    createFileIfNone(fileName)

    # Over-write the file with the given number and close it
    file = open(fileName,"w")
    file.seek(0)
    file.write(newNumber)
    file.truncate(len(newNumber))
    file.close()

"""
Adds to the current state of a given file.
"""
def incrementCurrentCounterState(fileName,incrementer):
    # Get the current state, add the incrementer, and write the file
    currentState = getCurrentCounterState(fileName)
    newState = str(int(currentState) + incrementer)
    setCurrentCounterState(fileName,newState)

"""
Class for serial input
"""
class SerialInput:
    fileName = ""
    missedIncrements = 0

    def __init__(self,serialCOM):
        self.serialCOM = serialCOM

    """
    Outputs a string to the serial output
    """
    def serialOutput(self,message):
        self.serialCOM.write(bytes(message,"utf-8"))

    """
    Invoked when a string is printed
    """
    def onSerialInput(self,message):
        # STARTUP - Print out the current state as SET:Integer
        # NAME - Resync with given name
        # INCREMENT - Increment state and output
        # MANUALADD - Increment state
        # MANUALSUB - De-increment state
        # CLEAR - Clears the state
        if message[0:7] == "STARTUP":
            self.baseName = message[8:]
            self.fileName = message[8:] + COUNTER_STATE_FILE_NAME_END
            lastState = getCurrentCounterState(self.fileName)
            self.serialOutput("SET:" + lastState)
        elif message[0:4] == "NAME":
            self.baseName = message[5:]
            self.fileName = message[5:] + COUNTER_STATE_FILE_NAME_END
            incrementCurrentCounterState(self.fileName,self.missedIncrements)
            self.missedIncrements = 0

            lastState = getCurrentCounterState(self.fileName)
            self.serialOutput("SET:" + lastState)
        elif message == "INCREMENT":
            if self.fileName == "":
                self.missedIncrements += 1
                self.serialOutput("GETNAME")
                return

            incrementCurrentCounterState(self.fileName,1)
            DataCollection.onEventOccurred(self.baseName)
        elif message == "MANUALADD":
            if self.fileName == "":
                self.missedIncrements += 1
                self.serialOutput("GETNAME")
                return

            incrementCurrentCounterState(self.fileName,1)
        elif message == "MANUALSUB":
            if self.fileName == "":
                self.missedIncrements -= 1
                self.serialOutput("GETNAME")
                return

            incrementCurrentCounterState(self.fileName,-1)
        elif message == "CLEAR":
            if self.fileName == "":
                self.serialOutput("GETNAME")
                return

            setCurrentCounterState(self.fileName,"0")
        elif message == "REFRESH":
            if self.fileName == "":
                self.serialOutput("GETNAME")
                return

            refreshedState = str(DataCollection.getEntriesCount(self.baseName))
            setCurrentCounterState(self.fileName,refreshedState)
            self.serialOutput("SET:" + refreshedState)





"""
Strips data from serial print to string
"""
def convertSerialLineToString(message):
    message = str(message)
    return message[2:len(message) - 5]

"""
Thread to run COM ports
"""
class SerialThread(threading.Thread):
    """
    Pass values for thread
    """
    def passVariables(self,serialCOM,id):
        self.serialCOM = serialCOM
        self.currentId = id

        print("Starting serial connection on port",self.currentId)
        self.start()

    """
    Start the thread
    """
    def run(self):
        try:
            # While it is connect, get the next line
            serialClass = SerialInput(self.serialCOM)
            while True:
                line = convertSerialLineToString(self.serialCOM.readline())
                serialClass.onSerialInput(line)
        except serial.serialutil.SerialException:
            print("Connection terminated on port", self.currentId)

if __name__ == '__main__':
    while True:
        # Every COM_REFRESH_TIME seconds, update the connected COMs
        for i in range(0,MAX_SERIAL_TO_CHECK + 1):
            try:
                # Create COM (will error if open or missing) and create thread
                serialCOM = serial.Serial('COM' + str(i),9600)
                newSerialThread = SerialThread(name="Thread-{}".format(i))
                newSerialThread.passVariables(serialCOM,i)
            except:
                # If creating COM fails, do nothing
                pass

        sleep(COM_REFRESH_TIME)


