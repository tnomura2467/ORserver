#!/usr/bin/env python
import roslib
roslib.load_manifest('detect_object')
import sys
import rospy
import cv2

import cv_bridge
import sensor_msgs.msg

import argparse
import numpy as np
import chainercv

import detect_object.srv
import util

import re

from detect_object.msg import YoloRes

import std_msgs.msg

class image_converter:
    def __init__(self, input_topic, output_topic, detect_object_service, label_format):
        self.detect_object_service = detect_object_service
        self.image_pub = rospy.Publisher(
            output_topic, sensor_msgs.msg.Image, queue_size=10)

        self.YoloPub=rospy.Publisher("rosunity",YoloRes,queue_size=10)  
        #type->rescustom topic->"tounity"

        self.bridge = cv_bridge.CvBridge()
        self.image_sub = rospy.Subscriber(
            input_topic, sensor_msgs.msg.Image,
            self.callback)
        self.label_format = label_format

    def callback(self, data):
        try:
            from timeit import default_timer as timer
            start = timer()
            res = self.detect_object_service(data)
            end = timer()
            print('Finished detection. (%f [sec])' % (end - start, ))


            resdata=YoloRes() #resdata type -> rescustom
            resdata.labels=str(res.labels)

            kariname=str(res.names)
	    kariname=kariname.strip("[""]")
	    
	    karilist=kariname.split(',')
	    #resdata.names=['','','','','']
            resdata.scores=str(res.scores)
            
            i=0;
            for region in res.regions:
                resdata.x_offset[i]=int(region.x_offset)
                resdata.y_offset[i]=int(region.y_offset)
                resdata.width[i]=int(region.width)
                resdata.height[i]=int(region.height)
		resdata.names[i]=karilist[i]
                i=i+1
            resdata.num=int(i)
            #print(type(resdata.names[0]))
            sys.stdout.flush()
        except cv_bridge.CvBridgeError as e:
            print(e)
            return

        cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        util.visualize_result_onto(cv_image, res, self.label_format)
        
        try:
            self.image_pub.publish(
                self.bridge.cv2_to_imgmsg(cv_image, "bgr8")
            )
            self.YoloPub.publish(resdata) #publich resdata
             
        except cv_bridge.CvBridgeError as e:
            print(e)

def main(args):
    print("Wait for the service 'detect_object'...")
    sys.stdout.flush()
    rospy.wait_for_service('detect_object')
    print("Finished.")
    sys.stdout.flush()
    detect_object_service = rospy.ServiceProxy(
        'detect_object', detect_object.srv.DetectObject)
    print("Invoke rospy.init_node().")
    sys.stdout.flush()


    #publ=rospy.Publisher("tounity",std_msgs.msg.String,queue_size=10)


    rospy.init_node('monitor_and_detect', anonymous=True)
    input_topic = rospy.resolve_name("input")
    output_topic = rospy.resolve_name("output")
    label_format = rospy.get_param('~label_format', '%(score).2f: %(name)s')
    print("input_topic: %s" % (input_topic,))
    print("output_topic: %s" % (output_topic,))
    sys.stdout.flush()
    ic = image_converter(input_topic, output_topic, detect_object_service, label_format)
    

    #publ=rospy.Publisher("tounity",std_msgs.msg.String,queue_size=10)

    #rospy.init_node('publisher',anonymous=True)



    try:
        print("Invoke rospy.spin().")
        sys.stdout.flush()
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)


