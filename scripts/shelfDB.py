#!/usr/bin/env python
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

#import std_msgs.msg
from std_msgs.msg import String

import mysql.connector
from mysql.connector import errorcode
import os

from time import sleep

print('Start!!')
Info=[[0 for i in range(6)] for j in range(20)]
objnum=0


def callback(data):
    #rospy.loginfo(rospy.get_caller_id()+"I heard %s",data.data)
    tf=data.data
    if(tf=="true"):
        imgPublisher()
        tf="false"

def listener():
    rospy.init_node('ShelfPub', anonymous=True)
    rospy.Subscriber("chatter", String, callback)
    print('Wait..')
    rospy.spin()


def imgPublisher():
    image=sqlconnect()
    rospy.init_node('ShelfPub', anonymous=True)
    pub = rospy.Publisher('shelfimg',Image, queue_size=10)
    pub2 = rospy.Publisher('shelfimg2',Image, queue_size=10)

    numpub = rospy.Publisher('shelfnum',String, queue_size=10)
    DBpub = rospy.Publisher('shelfDB',DBinfo, queue_size=10)

    bridge = CvBridge()
    msg = bridge.cv2_to_imgmsg(image[0], encoding="bgr8")
    msg2 = bridge.cv2_to_imgmsg(image[2], encoding="bgr8")
    str2=str(Info[0][0])
    DBdata=DBinfo()

    for i in range(20):
        DBdata.Frame[i]=Info[i][0]
	DBdata.id[i]=Info[i][1]
	DBdata.Xmin[i]=Info[i][2]
	DBdata.Ymin[i]=Info[i][3]
	DBdata.Width[i]=Info[i][4]
	DBdata.Height[i]=Info[i][5]



    rate = rospy.Rate(0.5)
    #print(str(Info[0][0]))
    print("Pulish")
    for k in range(2):
        #numpub.publish(str2)
	DBpub.publish(DBdata)
	rate.sleep()

    for i in range(3):
        pub.publish(msg)
	pub2.publish(msg2)
        rate.sleep()
    print("finish")
    print('Wait...')



def sqlconnect():
    #Input userinfo
    config = {
            'user': 'tnomura',
            'password': 'interface123',
            'host': '10.40.0.95',
            'charset':'binary',
            }

    #connect MySQL
    

    try:
        cnx = mysql.connector.connect(**config)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('Cannnot connect database.')
        else:
            print(err)
    else:
	
	cursor = cnx.cursor()
	#DB_NAME = 'Holotest01'
	DB_NAME = args.dbname
	TBL_NAME = 'maintable'
    
	#create File
	path='data/'+DB_NAME
	if not os.path.exists('data'):
            os.mkdir('data')
	if not os.path.exists(path):
            os.mkdir(path)
	if not os.path.exists(path+'/txtfile'):
            os.mkdir(path+'/txtfile')
	if not os.path.exists(path+'/ppmfile'):
            os.mkdir(path+'/ppmfile')


        cursor.execute('USE {}'.format(DB_NAME))


        #issue query
        query = ("SELECT FrameCount, ObjectCount, Xmin, Ymin, Width, Height,ColorImage FROM {} "
             ).format(TBL_NAME)
        cursor.execute(query)
        objnum=0
        for row in cursor.fetchall():

	    Info[objnum][0]=row[0]
            Info[objnum][1]=row[1]
	    Info[objnum][2]=row[2]
	    Info[objnum][3]=row[3]
            Info[objnum][4]=row[4]
	    Info[objnum][5]=row[5]
	    ColorImage=row[6]
	
            #save text      
	    fTxt=open(path+'/txtfile/'+'TXT_'+str(i)+'.txt','w')
	    fTxt.write(str(row[0])+'\n'+str(row[1])+'\n'
	    +str(row[2])+'\n'+str(row[3])+'\n'+str(row[4])+'\n'
            +str(row[5]))
	    fTxt.close

            #save img
	    fImage=open(path+'/ppmfile/'+'IMAGE_'+str(i)+'.ppm','w')
	    fImage.write(row[6])
	    fImage.close
	    fImage.seek(0)
	    objnum=objnum+1
        cnx.close()

    shelf = cv2.imread('data/ImageFile/Shelf.jpg')
    Com=shelf
    im=[None for _ in range(20)]

    for num in range(i):
        im[num] = cv2.imread('data/'+DB_NAME+'/ppmfile/IMAGE_'+str(num)+'.ppm')
        #Com[Info[num][3]:Info[num][3]+Info[num][5],Info[num][2]:Info[num][2]+Info[num][4]] = im[num]


    ComCut=Com[100:230,110:290]
    #ComCut=Com[100:230,110:190]
    return im

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description='ROS services for detect objection.',
    )
    parser.add_argument('--dbname', default='test04',
                        help = 'name of DataBase')

    args = parser.parse_args()

    print(args.dbname)
    listener()












