#-------------------------------------------------------------------------------
# Name:        Create_CamSync.py
#
# Purpose:      This script is to be run in the DC_* camera folder created for the RCD30. This script will create
#               a CameraSync_%s_0.dat and a CameraSync_%s_R.dat.  The first file will be used when running
#               CZMIL_Image_Index. CZMIL_Image_Index creates it's own CameraSync_%s_T.dat file, which is the same
#               as the *_R.dat file but just a name change.  The point here is the files are the same but chartsPic
#               will recognize the files differently and apply the appropriate logic when using chartsPic in pfm3D Edit.
#
# Requirements:  Python 2.7 (standard library); pyproj, numpy, pandas
#
# Author:      J. Heath Harwood;
#
# Created:     10/20/2016
# Copyright:   (c) USACE 2016
# Licence:     Public
#
# Change Log:
#
#-------------------------------------------------------------------------------

###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.Import.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

import os
import math
from math import *
from datetime import *
import time
import glob
from pyproj import Proj, transform
import numpy as np
import pandas as pd


###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.CONST.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###
WEEK_OFFSET = 7.0 * 86400.0
prev_time = -1

###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.Functions.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

def getPictureTime(yr, mth, day, gps_seconds, prevTime):

    """
    :Pass the gps seconds of the image to get the unix time (picture time):
    :return:
    """

    try:

        # Define flight date using the folder name and strip the time to create a time struct
        flightDate = time.strptime((("%2s/%2s/%4s")%(mth,day,yr)), "%m/%d/%Y")

        # Get seconds from the epoch (01-01-1970) for the date in the filename. This will also give us the day of the
        # week for the GPS seconds of week calculation.
        tv_sec = time.mktime(flightDate)
        #print "GPS seconds from the epoch (01-01-1970) for the date in the filename :", tv_sec

        # Subtract the number of days since Saturday midnight (Sunday morning) in seconds.
        flightDate_weekday = flightDate.tm_wday + 1
        tv_sec = tv_sec - (flightDate_weekday * 86400)
        start_week = tv_sec
        #print "Subtract the number of days since Saturday midnight (Sunday morning) in seconds. :", start_week
        #print "The number of GPS Seconds is: ", gps_seconds

        picture_time = (start_week + gps_seconds) * 1000000.0
        #print "The new Picture time is: ", str(int(picture_time))
        #print "The previous Picture time is: ", str(int(prevTime))

        # Test for GPS Week Rollover
        if int(picture_time) < int(prevTime):
            picture_time += WEEK_OFFSET * 1000000.0
            print "The picture time after week rollover is: %s" % str(int(picture_time))
            return str(int(picture_time))
        else:
            print "The picture time before week rollover is: %s" % str(int(picture_time))
            return str(int(picture_time))


    except IOError as e:                                                            # prints the associate error
        print "I/O Error %d: %s" % (e.errno, e.strerror)
        raise e


###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.Main.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

#zoneNum = raw_input('\nWhat is the zone number?  Enter here: ')
zoneNum = 17
#zoneHem = raw_input('\nWhat is the zone hemisphere?  Enter here: ')
zoneHem = 'N'

# Figure out where you are
cwd = os.getcwd()
cwf = os.path.basename(cwd)

year = "20" + str(cwf[8:10])
month = str(cwf[10:12])
day = str(cwf[12:14])

# Open the CameraSync dat file

datFiles = glob.glob('*.dat')
for datFile in datFiles:
    datFile = datFile
    #print datFile

evtFiles = glob.glob('*.evt')
for evtFile in evtFiles:
    evtFile = evtFile
    #print evtFile

# Create a new output camera file that's merged with the event.evt and the coarse_lat_lon_ellHeight_roll_pitch_heading.dat
newDat = open((datFile.split('.')[0] + '_new' + '.dat'), 'w')

a1 = pd.read_csv(datFile, delimiter=r"\s+", header= None)
b1 = pd.read_csv(evtFile, delimiter=r"\s+", header= None)

a1[8] = b1[0]

a1.to_csv(newDat,index=False,header=False, sep=' ')

newDat.close()

# Open the new camera dat file for reading
newDatFiles = glob.glob('*_new.dat')
for newDatFile in newDatFiles:
    newDatFile = newDatFile
    #print newDatFile

camDat = open(newDatFile, 'r')
#print camSYNCdat
ilist = camDat.readlines()
#print ilist

# Name the output files from the name of the common working directory "DC_*"
csfName = str(cwf[8:])
#print csfName

# Create the output camera sync file that will be used for RCD30 Image Index
cameraSync0 = open(("CameraSync_" + csfName + '_0.dat'), 'w')
cameraSyncR = open(("CameraSync_" + csfName + '_R.dat'), 'w')
#print cameraSync

# Initialize a line counter
counter = 0
for iLine in ilist:

    if counter >= 0:

        # Gets the columns items to create a list
        mylist = iLine.strip().split(' ')
        mylist = [item for item in mylist if item]

        # Parse the data in the coarse_lat_lon_ellHeight_roll_pitch_heading_new.dat file
        pid = mylist[0]
        fileName = mylist[1].split('.')[0]
        #print "The name of the image file is: " + str(fileName)
        iName = os.path.join(fileName + '.jpg')
        lat = float(mylist[3])
        latF = format(lat, '.11f')
        lon = float(mylist[2]) - 360
        lonF = format(lon, '.11f')
        zed = float(mylist[4])
        zedF = format(zed, '.4f')
        pitch = float(mylist[6])
        pitchF = format(pitch, '.13f')
        roll = float(mylist[5])
        rollF = format(roll, '.13f')
        heading = float(mylist[7])
        headingF = format(heading, '.13f')
        gpsSeconds = float(mylist[8])
        gpsSecondsF = format(gpsSeconds, '.5f')
        picTime = getPictureTime(year, month, day, gpsSeconds, prev_time)
        #print picTime
        prev_time = picTime


        # Convert center Lat, Long to UTM
        p = Proj(proj='utm',zone=zoneNum,ellps='WGS84')
        cenEast, cenNorth =  p(lon,lat)
        cenEastF = format(cenEast, '.11f')
        cenNorthF = format(cenNorth, '.11f')

        # Contructs the string list for use in the Original Camera Sync file associated with HF and
        # the RCD30 Camera Sync file with that same formatting; 0 file can be used in
        camLines0 = (' %-20s  %60s  %-13s  %-13s  %-10s  -1  -1  -1  %s  %s  %-14s  %-15s  %-13s  %16s  %16s  %-14s  \n')%(pid, iName, cenEastF, cenNorthF, zedF, zoneNum, zoneHem, latF, lonF, gpsSecondsF, rollF, pitchF, headingF)
        camLinesR = (' %-20s  %60s  %-13s  %-13s  %-10s  -1  -1  -1  %s  %s  %-14s  %-15s  %-13s  %16s  %16s  %-14s  %-16s  \n')%(pid, iName, cenEastF, cenNorthF, zedF, zoneNum, zoneHem, latF, lonF, gpsSecondsF, rollF, pitchF, headingF, picTime)

        cameraSync0.writelines(camLines0)
        cameraSyncR.writelines(camLinesR)

        # Increment counter
        counter += 1

cameraSync0.close()
cameraSyncR.close()
