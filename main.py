import time
import datetime
import re
import serial

#秒より下の数字はいらないので必要な部分のみを取り出すための正規表現のパターン
pattern = r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}" 

#俺的曜日表現
weekDayConvList = ["GETU","KA","SUI","MOKU","KIN","DOU","NITI"]

#シリアルポートオープン
with serial.Serial('COM3',9600,timeout=1) as ser:
    oldDatetime = re.match(pattern,str(datetime.datetime.now())).group() #前の時刻
    while True:
        newDatetime = re.match(pattern,str(datetime.datetime.now())).group() #新しい時刻
        if newDatetime != oldDatetime: #意味的には一秒以上の変化があったとき、やってることは異なるか比較している
            oldDatetime = newDatetime #前の時刻を更新
            weekDayInt = datetime.datetime.now().weekday() #曜日取得

            #ここで実際に送信する文字列を組み立てる。年-月-日 (曜日) 時:分:秒 のフォーマット
            sendStr = \
                "\n\n\n" + re.search(r"\d{4}.\d{2}.\d{2}",newDatetime).group() +\
                "(" +weekDayConvList[weekDayInt] + ")" + "\n" + \
                re.search(r"\d{2}:\d{2}:\d{2}",newDatetime).group()
                
            print(sendStr) #念のために表示
            flag=bytes(sendStr,'utf-8') #バイト型に変換
            try:
                ser.write(flag) #送信
            
            #よくわからんが何かシリアル通信で例外が発生したら、メッセージ表示して終了
            except serial.serialutil.SerialException:
                print("Arduinoとの接続を確認してください。")
                break

            #シリアル通信:送信
        time.sleep(0.1) #このループを0.1秒間隔で行う
    ser.close()