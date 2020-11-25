#!/usr/bin/env python
# coding: utf-8
import roslib
roslib.load_manifest('detect_object')
import sys
import rospy
import cv2
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
from detect_object.msg import DBinfo
from std_msgs.msg import String
import mysql.connector
from mysql.connector import errorcode
import os
from time import sleep
cnt=1

def callback(data):
    uc=data.data
    if(uc=="whatNo"):

        countPublisher()
        uc="DonePub"

def listener():
    rospy.init_node('CountPub', anonymous=True)
    rospy.Subscriber("usercount", String, callback)
    print('Wait_usercount')
    rospy.spin()

def countPublisher():
    global cnt
    rospy.init_node('CountPub', anonymous=True)
    userNopub = rospy.Publisher('countNo',String, queue_size=10)
    userNo = str(cnt)

    print(userNo)

    rate = rospy.Rate(0.5)
    for k in range(2):
        userNopub.publish(userNo)
        rate.sleep()
    cnt=cnt+1


if __name__ == "__main__":
    listener()
