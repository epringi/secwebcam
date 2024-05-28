#!/usr/bin/env python3
#
#  This script uses a camera capture device, such as a webcam, and turns it
#  into a rudimentary motion sensing security camera, that records video
#  footage when activated.  Footage is saved to disk either when script is
#  terminated or if the footage reaches maxsavedframes.
#
#  Recording activates when the threshold number is hit and the thresholdframes
#  frame count has been hit.  Recording stops when x amount of frames (defined
#  in maxframes) are below the threshold.  Recording activates again once the
#  framebuffer has filled and the threshold wait frame count has been hit.
#
#  Secwebcam will log when recording starts and stops if the logfile exists
#  and it has permission to write to it.
#
#  Currently the only way to stop the script is to terminate it via SIGINT.
#
#  Variables you can change (description at each variable in code):
#
#  - camdevice: The capture device, default is 0, but if you have more than one
#  video capture device then change this to suit.
#
#  - maxframes: Max frames to keep in the frame buffer.  This is also the number
#  of preceding frames that are added to the recording when the movement
#  threshold is met.
#
#  - threshold: Movement threshold, default is 15, the lower the number the more
#  sensitive it is.  Under test conditions, highest recorded was 351, lowest was
#  0.  An unmoving image, like someone staring at a computer, usually records a
#  threshold from 4 to 12. Same person waving a hand at the screen records about
#  up to 22.
#
#  - thresholdframes: The number of consecutive frames that pass the threshold
#  before recording starts. Default is 1.
#
#  - maxsavedframes: Maximum amount of frames to save to one video file, default
#  is 1000.
#
#  - minfreespace: Minimum free space on HDD in GB that must be available before
#  a write operation (integer).
#
#  - logfile: Full path and name of the logfile to write to.
#
#  - font: The font for the timestamp
#
#
#  **NOTICE**
#  Please make sure you have enough storage space to keep all the recorded video!
#  If you set the threshold too low, it will be very sensitive and activate often,
#  which means it will be recording a lot of video data.  There is a disk space
#  check, use this to help avoid catastrophe. :P
#  ** WINDOWS NOT SUPPORTED for disk space check **
#
#  Liz Pringi, May 2024
#

import cv2, numpy as np, signal, sys, os
from datetime import datetime
import shutil

# The capture device, default is 0, but if you have more than one video capture
# device then change this to suit.
camdevice=0
# Max frames to keep in the frame buffer.  This is also the number of preceding
# frames that are added to the recording when the movement threshold is met.
maxframes=15
# Movement threshold, default is 15, the lower the number the more sensitive it is.
# Under test conditions, highest recorded was 351, lowest was 0.
# An unmoving image, like someone staring at a computer, usually records a
# threshold from 4 to 12. Same person waving a hand at the screen records about up to 22.
threshold=15
# The number of consecutive frames that pass the threshold before recording starts.
# Default is 1.
thresholdframes=1
# Maximum amount of frames to save to one video file, default is 1000.
maxsavedframes=1000
# Minimum free space on HDD in GB that must be available before a write operation (integer).
minfreespace=1
# Path
# Full path and name of the logfile to write to.
logfile="/var/log/secwebcam/motion.log"
# The font for the timestamp
font=cv2.FONT_HERSHEY_SIMPLEX

# Don't change these values
recording=False
savedframes=[]
quietlen=0
framebuffer=[]

logging=True
try:
  open(logfile, 'a')
except PermissionError:
  print("Unable to open logfile, check permissions.  Logging disabled.")
  logging=False
except FileNotFoundError:
  print("Unable to open logfile, check that directory exists.  Logging disabled.")
  logging=False

diskcheck=True

try:
  working_dir=os.path.dirname(os.path.realpath(__file__))
  total, used, free = shutil.disk_usage(working_dir)
except FileNotFoundError:
  print("Free disk space check not available.")
  diskcheck=False

cam=cv2.VideoCapture(camdevice)
# Uncomment and adjust the below lines with a different resolution if you prefer.
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640.0)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480.0)
cam.set(cv2.CAP_PROP_FPS, 30.0)

# Initialise the frame buffer with the first <maxframes> frames
for i in range(0, maxframes):
  _, frame=cam.read()
  # Put timestamp on frame:
  # putText(frame, text, (posx, posy), font, font_size, (r, g, b), thickness, line_type[LINE_4, LINE_8, LINE_AA, FILLED])
  cv2.putText(frame, datetime.now().strftime("%H:%M:%S %d-%m-%Y"), (10, 30), font, 1.005, (0, 0, 0), 3, cv2.LINE_AA)
  cv2.putText(frame, datetime.now().strftime("%H:%M:%S %d-%m-%Y"), (11, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
  framebuffer.append(frame)

# Handle logging
def logwrite(msg):
  log=open(logfile, 'a')
  log.write("".join([str(msg), '\n']))
  log.close()

# Calculation for determining the diff between frames
def framediff(frame1, frame2):
  frame1=cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
  frame2=cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
  diff=cv2.subtract(frame1, frame2)
  h, w=frame1.shape
  diff=np.sum(diff)
  diff=int(diff/((h/2)*(w/2)))

  return diff

def savetofile():
  global savedframes

  # Check disk space before saving
  writable=True
  if diskcheck==True:
    working_dir = os.path.dirname(os.path.realpath(__file__))
    total, used, free = shutil.disk_usage(working_dir)
    if ((free//1024)//1024)//1024 < minfreespace:
      writable=False
  if diskcheck==True and writable==False:
    cam.release()
    if logging==True:
      logwrite("[%s] HDD space below %iGB.  Frames not saved." %(str(datetime.now().strftime("%H:%M:%S %d-%m-%Y")), minfreespace))
    print("HDD space below %iGB.  Frames not saved." %(minfreespace))
    exit(1)
  h, w, _=savedframes[0].shape
  size=(w, h)
  # Init output file
  camout=cv2.VideoWriter("%s.avi" %(str(datetime.now().strftime("%d-%m-%Y.%H-%M-%S"))), cv2.VideoWriter_fourcc(*'MJPG'), cam.get(cv2.CAP_PROP_FPS), size)
  for frame in savedframes:
    camout.write(frame)
  # Close output file
  camout.release()
  if logging==True:
    logwrite("[%s] %i frames saved." %(str(datetime.now().strftime("%H:%M:%S %d-%m-%Y")), len(savedframes)))
  print(len(savedframes), "frames saved.")
  savedframes=[]

# sigint to quit, save and release cam device
def signal_handler(sig, exframe):
  savetofile()
  cam.release()
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

cooldown=maxframes
thresholdframecount=0

if thresholdframes<1:
  thresholdframes=1

print("Init complete.")

while True:
  _, frame=cam.read()
  # Add the timestamp
  cv2.putText(frame, datetime.now().strftime("%H:%M:%S %d-%m-%Y"), (10, 30), font, 1.005, (0, 0, 0), 3, cv2.LINE_AA)
  cv2.putText(frame, datetime.now().strftime("%H:%M:%S %d-%m-%Y"), (11, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

  # Check thresholdframes variable.  Add to it if the frame passes the threshold, put it to 0 if it does not.
  if recording==False and thresholdframecount<thresholdframes and framediff(frame, framebuffer[maxframes-1])>=threshold:
    thresholdframecount+=1
  elif recording==False and framediff(frame, framebuffer[maxframes-1])<threshold:
    thresholdframecount=0
  # Start recording if we reach the movement threshold, and add the framebuffer to the saved frames.
  if recording==False and cooldown>=maxframes and thresholdframecount>=thresholdframes:
    if logging==True:
      logwrite("[%s] Started recording" %(str(datetime.now().strftime("%H:%M:%S %d-%m-%Y"))))
    print("Started recording at", datetime.now().strftime("%H:%M:%S %d-%m-%Y"))
    savedframes.extend(framebuffer)
    thresholdframecount=0
    recording=True
  # If we're recording, add the current frame.
  if recording==True and quietlen<maxframes:
    savedframes.append(frame)
  # Check if the threshold has been reached and we have to reset the length of quiet frames
  if recording==True and framediff(frame, framebuffer[maxframes-1])>=threshold and quietlen>0:
    quietlen=0
  # Increment the quiet frames counter if the frame diff is under threshold.
  elif recording==True and framediff(frame, framebuffer[maxframes-1])<threshold:
    quietlen+=1
  # Stop recording if video has been quiet as long as maxframes, and start cooldown.
  if quietlen>maxframes-1 and recording==True:
    if logging==True:
      logwrite("[%s] Stopped recording" %(str(datetime.now().strftime("%H:%M:%S %d-%m-%Y"))))
    print("Stopped recording at", datetime.now().strftime("%H:%M:%S %d-%m-%Y"))
    recording=False
    cooldown=0
  if recording==False and cooldown<maxframes:
    cooldown+=1

  # Pop off the first frame, then add the latest frame to the buffer.
  framebuffer.pop(0)
  framebuffer.append(frame)

  if len(savedframes)>maxsavedframes-1:
    savetofile()