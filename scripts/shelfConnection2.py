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
# import detect_object.srv
# import util
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

'''
# 適宜書き換えが必要な部分
> Initial Input Data
- db_user
    : 接続するデータベースのユーザー名
​
- db_password
    : 接続するデータベースで登録したパスワード
​
- db_host
    : 接続するデータベースが稼働しているマシンのホスト
​
- db_dbname
    : 利用するデータベース名
​
- db_table
    : 利用するテーブル名

- pubcount
    : 画像をpublishする回数

-----
# Topic
- shelfori
    : 元の棚画像(3D Shelfでは必要なし)
​
- shelfDB
    : 検知した物体情報
​
- shelfimg{$i}
    : 検知した物体画像
'''

# ----- Initial input data -----
db_user = "tnomura"
db_password = "interface123"
db_host = "10.40.0.95"

db_dbname = "bri3"
db_table = "maintable"

pubcount = 2
# ------------------------------



print('Start!!')
# 11 × 20 の配列を作成 | DBデータを保持
Info = [[0 for i in range(11)] for j in range(20)]

# 20 の配列を作成 | publisherの内容を保持
pub = [None for _ in range(20)]

# 20 の配列を作成 | publishするメッセージを保持
msg = [None for _ in range(20)]

cntone = 0
objnum = 0

# データベースにアクセスし物体の情報を取得する関数
def sqlconnect():
    # Input userinfo
    config = {
            'user': db_user,
            'password': db_password,
            'host': db_host,
            'charset':'binary',
            }

    # connect MySQL
    print('try connect database')

    try:
        cnx = mysql.connector.connect(**config)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('Cannnot connect database.')
        else:
            print(err)
    else:
        print('Success connect database!')

    cursor = cnx.cursor()
    DB_NAME = db_dbname
    TBL_NAME = db_table
    """
	# create File
    home_path = os.path.expanduser('~')
    rosdb_full_path = home_path + '/catkin_ws/src/detect_object/scripts/data/' + DB_NAME
    os.makedirs(rosdb_full_path + '/txtfile', exist_ok=True)
    os.makedirs(rosdb_full_path + '/ppmfile', exist_ok=True)"""
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

    # issue query
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
        # save text
        fTxt=open(path+'/txtfile/'+'TXT_'+str(objnum)+'.txt','w')
        fTxt.write(str(row[0])+'\n'+str(row[1])+'\n'+str(row[2])+'\n'+str(row[3])+'\n'
	    +str(row[4])+'\n'+str(row[5])+'\n'+str(row[6])+'\n'
            +str(row[7])+'\n'+str(row[8])+'\n'+str(row[9])+'\n'+str(row[10]))
        fTxt.close

        # save img
        fImage=open(path+'/ppmfile/'+'IMAGE_'+str(objnum)+'.ppm','wb')
        fImage.write(row[11])
        fImage.close
        fImage.seek(0)
        objnum=objnum+1
    cnx.close()

    im=[None for _ in range(20)]

    for num in range(objnum):
        im[num] = cv2.imread(path + '/ppmfile/IMAGE_'+str(num)+'.ppm')

    return im


def dbinputdata():
    print("--DataBase usage information--")
    print("User : " + db_user)
    if(args.PW == "open"):
        print("Password : " + db_password)
    else:
        print("Password : " + "*")
    print("Host : " + db_host)
    print("DBNAME : " + db_dbname)
    print("TABLE : " + db_table)
    print("------------------------------")


# HoloLensから"true"という文字がPublishされたらimgPublisher関数に入る
def callback(data):
    #rospy.loginfo(rospy.get_caller_id()+"I heard %s",data.data)
    tf=data.data
    if(tf=="true"):
        print("subscribe chatter")
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
    # sqlconnect関数に入り物体情報を取得
    global cntone
    image=sqlconnect()
    # 初期化 : ソフトウェア名は「ShelfPub」
    rospy.init_node('ShelfPub', anonymous=True)
    # nodeの宣言 : publisherのインスタンスを作成
    # 「shelfori」というTopicにImage型のメッセージを送るPublisherの作成
    #pubshelf = rospy.Publisher('shelfori',Image, queue_size=10)

    # Topic「shelfDB」に[detect_object/msg/DBinfo.msg]型のメッセージを送るPublisherの作成
    DBpub = rospy.Publisher('shelfDB',DBinfo, queue_size=10)

    bridge = CvBridge()
    DBdata=DBinfo()

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

    DBdata.cnt=dbcnt

    print('DBdataカウント数', DBdata.cnt)

    for i in range(0,DBdata.cnt):
        # Topic「shelfimg$i」にImage型のメッセージを送るPublisherの作成
        pub[i]=rospy.Publisher('shelfimg'+str(i),Image, queue_size=10)

    #shelfOri=bridge.cv2_to_imgmsg(shelfCut, encoding="bgr8")
    for i in range(0, DBdata.cnt):
        # sqlconnectの返り値をimgmsg形式に変換
        msg[i] = bridge.cv2_to_imgmsg(image[i], encoding="bgr8")

    if(cntone==0):
        # まず物体のサイズや座標などの情報をpublish
        rate = rospy.Rate(0.5)
        print("Pulish")
        for k in range(pubcount):
            DBpub.publish(DBdata)
            rate.sleep()

    # 物体の画像をpublish
        for i in range(pubcount):
            #pubshelf.publish(shelfOri)
            for i in range(0, DBdata.cnt):
                pub[i].publish(msg[i])
            rate.sleep()
        print("finish")
        print('Wait...')
        cntone=1
    # 再びHoloLensからの合図があるまで待機

if __name__ == "__main__":
    # コマンドライン引数で表示内容変更
    parser = argparse.ArgumentParser(
        description='show password',
    )
    parser.add_argument('--PW', default='close',
                        help = 'closed now')

    args = parser.parse_args()

    # DB情報を表示
    dbinputdata()

    # sqlconnect()
    # ノードが終了するまで、自ノードを終了させないように待機
    listener()
