# secwebcam
This script uses a camera capture device, such as a webcam, and turns it
into a rudimentary motion sensing security camera, that records video
footage when activated.  Footage is saved to disk either when script is
terminated or if the footage reaches maxsavedframes.

Recording activates when the threshold number is hit and the thresholdframes
frame count has been hit.  Recording stops when x amount of frames (defined
in maxframes) are below the threshold.  Recording activates again once the
framebuffer has filled and the threshold wait frame count has been hit.

Secwebcam will log when recording starts and stops if the logfile exists
and it has permission to write to it.

Currently the only way to stop the script is to terminate it via SIGINT.


Variables you can change (description at each variable in code):

- camdevice: The capture device, default is 0, but if you have more than one
video capture device then change this to suit.

- maxframes: Max frames to keep in the frame buffer.  This is also the number
of preceding frames that are added to the recording when the movement
threshold is met.

- threshold: Movement threshold, default is 15, the lower the number the more
sensitive it is.  Under test conditions, highest recorded was 351, lowest was
0.  An unmoving image, like someone staring at a computer, usually records a
threshold from 4 to 12. Same person waving a hand at the screen records about
up to 22.

- thresholdframes: The number of consecutive frames that pass the threshold
before recording starts. Default is 1.

- maxsavedframes: Maximum amount of frames to save to one video file, default
is 1000.

- minfreespace: Minimum free space on HDD in GB that must be available before
a write operation (integer).

- logfile: Full path and name of the logfile to write to.

- font: The font for the timestamp


**NOTICE**
Please make sure you have enough storage space to keep all the recorded video!
If you set the threshold too low, it will be very sensitive and activate often,
which means it will be recording a lot of video data.  There is a disk space
check, use this to help avoid catastrophe. :P
** WINDOWS NOT SUPPORTED for disk space check **