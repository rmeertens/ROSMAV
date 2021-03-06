#!/usr/bin/env python
import roslib
import time
import sys
roslib.load_manifest(sys.argv[0].split('/')[-2])
import rospy
from std_msgs.msg import String, Empty
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image, CameraInfo
from cmvision.msg import Blobs, Blob
from getat import getat
import heatmap
import numpy as np

import cv
from cv_bridge import CvBridge, CvBridgeError
bridge = CvBridge()
hm_pub = rospy.Publisher("/heatmap_image", Image)
hm_enc_pub = rospy.Publisher("/heatmap_image/encoding", String)

action = rospy.Publisher("cmd_vel", Twist)

rospy.init_node('v', anonymous=True)

WIDTH = 320
HEIGHT = 240
MIDPOINTX = 160

directionz = 1

C_LIGHT = (253, 255, 253)
C_TARGET = (0,  182,  234)

target_heatmap = np.zeros(shape=(240/heatmap.downsize_factor, 320/heatmap.downsize_factor), dtype=np.int8)
indexes = np.array(range(320/heatmap.downsize_factor))


#Specifies whether a given color is red by looking at the RGB values
def isRed(c):
	return c[0] > 150
#Specifies whether a given color is green by looking at the RGB values
def isGreen(c):
	return c[1] > 50 and c[1] < 150 and c[0] < 50 and c[2] < 50 and c[2] < 150
#Specifies whether a given color is blue by looking at the RGB values
def isBlue(c):
	return c[0] < 180 and c[1] > 150
#Specifies whether a given color is yellow by looking at the RGB values
def isYellow(c):
	return c[0] > 150 and c[1] > 150 and c[2] < 200

def finished(c): return False

currentTarget = isRed
nextTarget = {isRed: isBlue, isBlue: isRed}
snelheid = 0

# Main decision function
def c(data):
	global directionz, currentTarget, snelheid
	if img is None:
		return
	lights = [x for x in data.blobs if getat(img, x)[0] > 100]
	if lights:
		naar = min(lights, key=lambda x: x.y)
		twist = Twist()
		twist.linear.x = .1
		if naar.x < 50:
			twist.angular.z = .7
			directionz = 1
			print "hard left"
		elif naar.y > WIDTH - 50:
			twist.angular.z = -.7
			directionz = -1
			print "hard right"
		elif naar.x < MIDPOINTX - 20:
			twist.angular.z = .3
			directionz = 1
			print "left"
		elif naar.x > MIDPOINTX + 20:
			twist.angular.z = -.3
			directionz = -1
			print "right"
		else:
			#twist.linear.x = .2
			print "straight on"
		action.publish(twist)
	else:
		twist = Twist()
		twist.angular.z = directionz
		#action.publish(twist)
		#print "n/a"
	print currentTarget.__name__
	targets = [x for x in data.blobs if currentTarget(getat(img, x))]
	heatmap.cooldown(target_heatmap)
	heatmap.draw(target_heatmap, targets)
	hm2 = 1 * target_heatmap
	hm2[hm2 < 80] = 0
	
	f = cv.fromarray(hm2)
	#print f, dir(f), f.step, f.channels, f.cols, f.rows, f.width, f.height
	hm_pub.publish(bridge.cv_to_imgmsg(f))
	hm_enc_pub.publish("16SC1")
	if targets:
		target = max(targets, key=lambda x: x.area)
		print target.area
		if target.area > 2500:
			#found!
			target_heatmap[:] = 0

			# If we have a new target after this one, take the next target. Otherwise we start landing
			if currentTarget in nextTarget:
				currentTarget = nextTarget[currentTarget]
			else:
				# Start landing
				twist = Twist()
				twist.linear.x = -.1
				action.publish(twist)
				l = rospy.Publisher("/ardrone/land", Empty)
				l.publish(Empty())
				print "found!"
				currentTarget = finished
	twist = Twist()
	if hm2.max() > 16:
		weights = np.apply_along_axis(np.sum, 0, hm2)
		loc = np.average(indexes, weights=weights)/len(indexes)
		if loc < .5:
			print "left (new)"
		else:
			print "right (new)"
		twist.linear.x = .1
		twist.angular.z = .5 - loc# - .5
	action.publish(twist)

img = None

# The img_get function is called every time the topic ardrone/img_raw fires. It saves the captured image to a global variable
def img_get(data):
	global img
	img = data

# Subscribes to the blobs and image from the AR Drone
rospy.Subscriber("/blobs", Blobs, c)
rospy.Subscriber("/ardrone/image_raw", Image, img_get)

# Main loop
try:
	rospy.spin()
except KeyboardInterrupt:
	print "Shutting down"

