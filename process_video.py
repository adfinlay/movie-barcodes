from __future__ import division
import subprocess as sp
import numpy
from PIL import Image, ImageDraw
import re
import time
import sys
import json
import os

outputWidth = 5000

print ""
print ""

# Timestamp so you can see how long it took
start_time = "Script started at " + time.strftime("%H:%M:%S")
print start_time

# optional starting time hh:mm:ss.ff; default value set to 00:00:00.0
hh = "%02d" % (0,)
mm = ":%02d" % (0,)
ss = ":%02d" % (0,)
ff = ".0"
print "Timestamp for first frame: "+hh+mm+ss+ff

filename = str(sys.argv[1])
outfilename = ""

if len(sys.argv) > 2:
    outfilename = sys.argv[2]
else:
    outfilename = os.path.splitext(filename)[0] + ".png"

print "Filename:", filename
print "Output filename:", outfilename

FFPROBE_BIN = "ffprobe"
command = [ FFPROBE_BIN,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            '-select_streams', 'v:0',
            filename]

print ""
print 'ffprobe command: ' + ' '.join(command);
print ""

# run the ffprobe process, decode stdout into utf-8 & convert to JSON
ffprobeOutput = sp.check_output(command).decode('utf-8')
ffprobeOutput = json.loads(ffprobeOutput)

nbFrames = 0

if len(ffprobeOutput['streams']) == 0:
    print "No video streams found in input file!"
    sys.exit(2)

format = ffprobeOutput['format']
stream = ffprobeOutput['streams'][0]

if 'nb_frames' in stream and int(stream['nb_frames']) > 0:
    nbFrames = int(stream['nb_frames'])
elif 'duration' in format and 'r_frame_rate' in stream:
    warning("Guessing number of frames from duration!")

    if stream['r_frame_rate'].find('/') != -1:
        fps_parts = stream['r_frame_rate'].split('/')
        nbFrames = int(float(format['duration']) * (float(fps_parts[0]) / float(fps_parts[1])))
    else:
        nbFrames = int(float(format['duration']) * float(stream['r_frame_rate']))
else:
    print "Can't determine number of frames!"
    sys.exit(2)

# calculate frame step
step = int(round(nbFrames / outputWidth))
sampleCount = int(round(nbFrames / step))

print "Frame Step:",step
print "Requested Output Width: {}px".format(outputWidth)
print "Actual Output Width:  {}px".format(sampleCount)

# find height and width
frameHeight = stream['height']
frameWidth = stream['width']

print "Video Dimensions: {}x{}px".format(frameWidth,frameHeight)
print "Frame Count:",nbFrames
print ""

###
### This section: credit to http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/

# Open the video file. In Windows you might need to use FFMPEG_BIN="ffmpeg.exe"; Linux/OSX should be OK.
FFMPEG_BIN = "ffmpeg"
command = [ FFMPEG_BIN,
            '-threads', '4',
            '-ss', hh+mm+ss,
            '-i', filename,
            '-filter:v', 'select=not(mod(n\,{})),setpts=N/(FRAME_RATE*TB)'.format(step),
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo', '-']

print ""
print 'ffmpeg command: ' + ' '.join(command);
print ""

pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

# get the average rgb value of a frame
def draw_next_frame_rgb_avg(raw_frame):
    frame =  numpy.fromstring(raw_frame, dtype='uint8')
    frame = frame.reshape((frameHeight,frameWidth,3))
    rgb_avg = int(numpy.average(frame[:,:,0])),int(numpy.average(frame[:,:,1])),int(numpy.average(frame[:,:,2]))
    return rgb_avg


# Go through the pipe one frame at a time until it's empty; store each frame's RGB values in rgb_list
rgb_list = []
x = 0 # optional; purely for displaying how many frames were processed
while True: # as long as there's data in the pipe, keep reading frames
    frame = pipe.stdout.read(frameWidth*frameHeight*3)

    if frame == '':
        break

    try:
        rgb_list.append(draw_next_frame_rgb_avg(frame))
        x = x + 1
    except:
        print "No more frames to process (or error occurred). Number of frames processed:", x


print ""
print "Lines to draw: {}".format(len(rgb_list))

# create a new image width the same width as number of frames sampled,
# and draw one vertical line per frame at x=frame number
image_height = int(len(rgb_list)*9/16)
new = Image.new('RGB',(len(rgb_list),image_height))
draw = ImageDraw.Draw(new)
# x = the location on the x axis of the next line to draw
x_pixel = 1
for rgb_tuple in rgb_list:
    draw.line((x_pixel,0,x_pixel,image_height), fill=rgb_tuple)
    x_pixel = x_pixel + 1

new.show()
new.save(outfilename)

print ""
print start_time
print "Script finished at " + time.strftime("%H:%M:%S")
