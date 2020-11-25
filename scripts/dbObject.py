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

#import std_msgs.msg
from std_msgs.msg import String

import mysql.connector
from mysql.connector import errorcode
import os

from time import sleep

print('Start!!')
Info=[[0 for i in range(11)] for j in range(20)]
imagenum=[None for _ in range(20)]
msg=[None for _ in range(20)]
cntone=0

pub=[None for _ in range(20)]


objnum=0
# 空の棚の画像取得
shelf = cv2.imread('data/ImageFile/or2shelf.jpg')
#棚の範囲指定
shelfCut=shelf[128:247,212:282]

# HoloLensから"true"という文字がPublishされたらimgPublisher関数に入る
def callback(data):
    #rospy.loginfo(rospy.get_caller_id()+"I heard %s",data.data)
    tf=data.data
    if(tf=="true"):
        imgPublisher()
        tf="false"

# 待機
def listener():
    rospy.init_node('ShelfPub', anonymous=True)
    rospy.Subscriber("chatter", String, callback)
    print('Wait..')
    rospy.spin()

# 物体画像をPublishする関数
def imgPublisher():
    #sqlconnect関数に入り物体情報を取得
    global cntone
    image=sqlconnect()
    rospy.init_node('ShelfPub', anonymous=True)
    pubshelf = rospy.Publisher('shelfori',Image, queue_size=10)

    """pub = rospy.Publisher('shelfimg',Image, queue_size=10)
    pub2 = rospy.Publisher('shelfimg2',Image, queue_size=10)
    pub3 = rospy.Publisher('shelfimg3',Image, queue_size=10)"""
    """pub[0]=rospy.Publisher('shelfimg',Image, queue_size=10)
    pub[1]=rospy.Publisher('shelfimg2',Image, queue_size=10)
    pub[2]=rospy.Publisher('shelfimg3',Image, queue_size=10)"""



    #numpub = rospy.Publisher('shelfnum',String, queue_size=10)
    DBpub = rospy.Publisher('shelfDB',DBinfo, queue_size=10)


    bridge = CvBridge()
    DBdata=DBinfo()
    idnum=0
    vecnum=0

    dbcnt=0
    for i in range(20):
        DBdata.FrameB[i]=Info[i][0]
        DBdata.FrameT[i]=Info[i][1]
        DBdata.TimeB[i]=Info[i][2]
        DBdata.TimeT[i]=Info[i][3]
        DBdata.id[i]=Info[i][4]
        DBdata.Xmin[i]=Info[i][5]
        DBdata.Ymin[i]=Info[i][6]
        DBdata.Width[i]=Info[i][7]
        DBdata.Height[i]=Info[i][8]
        DBdata.Depth[i]=Info[i][9]
        DBdata.Yobi[i]=0
        DBdata.YobiYobi[i]=0
        if(Info[i][9]==0):
            break
        dbcnt=dbcnt+1



        """if(Info[i][1]==idnum):
            if(Info[i][7]==1):
                imagenum[vecnum]=i
                DBdata.WhatNo[vecnum]=i
                idnum=idnum+1
                vecnum=vecnum+1
            elif(Info[i][7]==2):
                idnum=idnum+1"""

    DBdata.cnt=dbcnt
    print(DBdata.cnt)
    #print(DBdata.WhatNo[0])
    #print(DBdata.WhatNo[1])
    for i in range(0,DBdata.cnt):
        pub[i]=rospy.Publisher('shelfimg'+str(i),Image, queue_size=10)

    shelfOri=bridge.cv2_to_imgmsg(shelfCut, encoding="bgr8")
    for i in range(0, DBdata.cnt):
        #print(imagenum[i])
        msg[i] = bridge.cv2_to_imgmsg(image[i], encoding="bgr8")

    """
    print(imagenum[1])
    msg2 = bridge.cv2_to_imgmsg(image[imagenum[1]], encoding="bgr8")
    print(type(image[4]))
    msg3 = bridge.cv2_to_imgmsg(image[imagenum[2]], encoding="bgr8")
    """

    if(cntone==0):
    # まず物体のサイズや座標などの情報をpublish
        rate = rospy.Rate(0.5)
    #print(str(Info[0][0]))
        print("Pulish")
        for k in range(2):
            DBpub.publish(DBdata)
            rate.sleep()

    # 物体の画像をpublish
        for i in range(2):
            pubshelf.publish(shelfOri)
            for i in range(0, DBdata.cnt):
                pub[i].publish(msg[i])
            rate.sleep()
        print("finish")
        print('Wait...')
        cntone=1
    # 再びHoloLensからの合図があるまで待機

# データベースにアクセスし物体の情報を取得する関数
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
        query = ("SELECT FrameCount,FrameTake,TImeBring,TimeTake, ObjectCount, Xmin, Ymin, Width, Height,Depth,TakeBring,ColorImage FROM {} "
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
            Info[objnum][6]=row[6]
            Info[objnum][7]=row[7]
            Info[objnum][8]=row[8]
            Info[objnum][9]=row[9]
            Info[objnum][10]=row[10]
            ColorImage=row[11]

            #save text
	    fTxt=open(path+'/txtfile/'+'TXT_'+str(objnum)+'.txt','w')
	    fTxt.write(str(row[0])+'\n'+str(row[1])+'\n'+str(row[2])+'\n'+str(row[3])+'\n'
	    +str(row[4])+'\n'+str(row[5])+'\n'+str(row[6])+'\n'
            +str(row[7])+'\n'+str(row[8])+'\n'+str(row[9])+'\n'+str(row[10]))
	    fTxt.close

            #save img
	    fImage=open(path+'/ppmfile/'+'IMAGE_'+str(objnum)+'.ppm','w')
	    fImage.write(row[11])
	    fImage.close
	    fImage.seek(0)
	    objnum=objnum+1
        cnx.close()

    #shelf = cv2.imread('data/ImageFile/Shelf.jpg')
    #Com=shelf
    im=[None for _ in range(20)]

    for num in range(objnum):
        im[num] = cv2.imread('data/'+DB_NAME+'/ppmfile/IMAGE_'+str(num)+'.ppm')

        #Com[Info[num][3]:Info[num][3]+Info[num][5],Info[num][2]:Info[num][2]+Info[num][4]] = im[num]


    #ComCut=Com[100:230,110:290]
    #ComCut=Com[100:230,110:190]
    return im

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='ROS services for detect objection.',
    )
    parser.add_argument('--dbname', default='closeshelf',
                        help = 'name of DataBase')

    args = parser.parse_args()

    print(args.dbname)
    listener()
