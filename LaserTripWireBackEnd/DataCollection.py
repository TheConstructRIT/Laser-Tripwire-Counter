"""
Local data collection used with laser trip wire backend

Author: Z. Cook
"""

import os
import time
import re
import DataSender

# End of file name to store last state
TIMESTAMP_DATA_FILE_NAME_END = "_SerialCounterTimestampData.txt"

"""
Checks if a file exists. If it doesn't, creates the file
"""
def createFileIfNone(fileName):
    # Check if the file exists
    if not os.path.exists(fileName):
        # Write a new file
        file = open(fileName,"w+")
        file.close()

"""
Adds leading zero to number if it doesn't have 2 digits
"""
def addLeadingZero(integer):
    integer = str(integer)
    if len(integer) == 1:
        return "0" + integer
    else:
        return integer

"""
Appends a timestamp in the given file
"""
def addEntryAtTimestamp(baseName):
    # Create file
    fileName = baseName + TIMESTAMP_DATA_FILE_NAME_END
    createFileIfNone(fileName)

    # Get time and date
    localTime = time.localtime()
    formattedTime = (addLeadingZero(localTime.tm_mon) + "/" + addLeadingZero(localTime.tm_mday) + "/"
                     + str(localTime.tm_year) + " " + addLeadingZero(localTime.tm_hour) + ":"
                     + addLeadingZero(localTime.tm_min) + ":" + addLeadingZero(localTime.tm_sec))

    # Store date
    file = open(fileName, "a")
    file.write(formattedTime + "\n")
    file.close()





"""
Returns integer concatenation for day, month, and year
"""
def dateToFormat(day,month,year):
    day,month,year = str(day),str(month),str(year)

    # Fix formatting
    if len(day) == 1:
        day = "0" + day

    if len(month) == 1:
        month = "0" + month

    # Return format
    return int(year + month + day)

"""
Converts an integer to a date (in month/day/year)
"""
def formatToDate(dateFormat):
    dateFormat = str(dateFormat)
    return dateFormat[-4:-2] + "/" + dateFormat[-2:] + "/" + dateFormat[0:-4]





"""
Parses the times into following format:
[
    {
        day = int (concat: year,month,day),
        hours = [
            {
                hour = int,
                times = int,
                timestamps = [...]
            }
        ]
    }
]
"""
def parseData(baseName):
    # Open file
    fileName = baseName + TIMESTAMP_DATA_FILE_NAME_END
    createFileIfNone(fileName)
    file = open(fileName, "r")

    parsedData = []
    """
    Get the hours list from the format
    """
    def getDateList(dateFormat):
        # Get existing entry
        for dateEntry in parsedData:
            if dateEntry.get("day") == dateFormat:
                return dateEntry["hours"]

        # Create new entry if it doesn't exist
        newDateEntry = {}
        newDateEntry["day"] = dateFormat
        newDateEntry["hours"] = []
        parsedData.append(newDateEntry)
        return newDateEntry.get("hours")

    """
    Get the hour entry from a list
    """
    def getHoursEntry(hoursList,hour):
        # Get existing entry
        for hourEntry in hoursList:
            if hourEntry["hour"] == hour:
                return hourEntry

        # Create new entry
        newHourEntry = {}
        newHourEntry["hour"] = hour
        newHourEntry["times"] = 0
        newHourEntry["timestamps"] = []
        hoursList.append(newHourEntry)
        return newHourEntry

    for line in file.readlines():
        line = line.strip()
        if line != "":
            # Get data for next line
            timeData = re.split('\D+',line)
            if len(timeData) >= 4:
                month,day,year = timeData[0],timeData[1],timeData[2]
                hour = int(timeData[3])
                dateFormat = dateToFormat(day,month,year)

                # Add entries
                hoursList = getDateList(dateFormat)
                hourEntry = getHoursEntry(hoursList,hour)

                # Add timestamp and increment by 1
                hourEntry["times"] += 1
                hourEntry["timestamps"].append(line)

    return parsedData

"""
Re-writes the log file and writes entries still within hour and returns entries to remove (see: parseData)
"""
def removeOldEntriesFromFile(baseName):
    parsedEntries = parseData(baseName)
    removedEntries = []
    keptEntries = []

    # Get local time
    localTime = time.localtime()
    day,month,year = localTime.tm_mday,localTime.tm_mon,localTime.tm_year
    hour = localTime.tm_hour
    dateFormat = dateToFormat(day, month, year)

    """
    Get the hours list from the format
    """
    def getHoursListInList(dateFormat,listToCheck):
        # Get existing entry
        for dateEntry in listToCheck:
            if dateEntry.get("day") == dateFormat:
                return dateEntry["hours"]

        # Create new entry if it doesn't exist
        newDateEntry = {}
        newDateEntry["day"] = dateFormat
        newDateEntry["hours"] = []
        listToCheck.append(newDateEntry)
        return newDateEntry.get("hours")

    for dateEntry in parsedEntries:
        if dateEntry["day"] < dateFormat:
            removedEntries.append(dateEntry)
        else:
            for hourEntry in dateEntry["hours"]:
                if hourEntry["hour"] < hour:
                    getHoursListInList(dateEntry["day"],removedEntries).append(hourEntry)
                else:
                    getHoursListInList(dateEntry["day"],keptEntries).append(hourEntry)

    return removedEntries,keptEntries

"""
Overrides the file with the given format of dates (see: parseData)
"""
def overrideFileWithNewEntries(parsedData,baseName):
    newFileData = ""

    # Set up new data for file
    for dateEntry in parsedData:
        for hourEntry in dateEntry["hours"]:
            for timestamp in hourEntry["timestamps"]:
                newFileData = newFileData + timestamp + "\n"

    # Override file
    fileName = baseName + TIMESTAMP_DATA_FILE_NAME_END
    file = open(fileName,"w")
    file.seek(0)
    file.write(newFileData)
    file.close()

"""
Sends out data for removed entries (see: parseData)
"""
def sendRemovedEntries(baseName,removedEntries):
    # Output timestamp and counts for hour intervals

    for dateEntry in removedEntries:
        dateFormat = formatToDate(dateEntry["day"])
        for hourEntry in dateEntry["hours"]:
            entryString = dateFormat + " " + str(hourEntry["hour"]) + ":00 - " + str(hourEntry["hour"]) + ":59"
            valueString = str(hourEntry["times"])

            DataSender.sendOutput(baseName,entryString,valueString)





"""
Invoked when event occurs to record a time stamp
"""
def onEventOccurred(baseName):
    addEntryAtTimestamp(baseName)
    removedEntries,keptEntries = removeOldEntriesFromFile(baseName)
    overrideFileWithNewEntries(keptEntries,baseName)
    sendRemovedEntries(baseName,removedEntries)

"""
Returns the number to display on the screen based on the unsent entries and sent entries
"""
def getEntriesCount(baseName):
    # Get database entries
    entriesCount = DataSender.getTotalInDatabase("Main Lab Laser")

    # Get stored entries
    removedEntries,keptEntries = removeOldEntriesFromFile(baseName)
    for dayEntry in keptEntries:
        for hourEntry in dayEntry["hours"]:
            entriesCount = entriesCount + hourEntry["times"]

    # Return entries
    return entriesCount