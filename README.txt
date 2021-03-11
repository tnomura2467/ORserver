tnomura2467/ORholo2 (棚内物体の仮想操作インタフェース)の実行時に動作させるサーバ

環境：Ubuntu18.04 ROSkinetic

roslaunch rosbridge_server rosbridge_websocket.launch

とrosrun detect_object dbObject.py --dbname dbnonamae　を実行（dbnonameはデータベースの名前）

