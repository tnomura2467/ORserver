#!/usr/bin/env python
import roslib
roslib.load_manifest('detect_object')
import sys
import rospy
import cv2

#import cv_bridge
#import sensor_msgs.msg
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import argparse
import numpy as np
import chainercv

import detect_object.srv
import util

import re

import linecache

from detect_object.msg import YoloRes

import std_msgs.msg

print('Hello')

im1 = cv2.imread('../../../../mySQLpython/data/test01/ppmfile/test01_maintableIMAGE_0.ppm')
shelf = cv2.imread('../../../../ImageFile/Shelf.jpg')

f=open('../../../../mySQLpython/data/test01/txtfile/test01_maintableTXT_0.txt')
data1=f.read()
f.close()
lines = data1.split('\n')
i=0
num=[None for _ in range(6)]
for line in lines:
    num[i]=int(line)
    i=i+1 

Com=shelf

Com[num[3]:num[3]+num[5],num[2]:num[2]+num[4]] = im1
#ComCut=Com[100:230,110:290]
ComCut=Com[100:230,110:190]




rospy.init_node('operator', anonymous=True)
pub = rospy.Publisher('Shelf_Image', Image, queue_size=10)
bridge = CvBridge()
msg = bridge.cv2_to_imgmsg(ComCut, encoding="bgr8")
rate = rospy.Rate(0.5)
while not rospy.is_shutdown():
        pub.publish(msg)
        rate.sleep()



