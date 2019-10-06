import time
import datetime
import re
import serial
import requests
import json


class Weather:
    def __init__(self):
        self.url = "http://weather.livedoor.com/forecast/webservice/json/v1"
        self.payload = {"city":"040010"} #http://weather.livedoor.com/forecast/rss/primary_area.xml ここに地域コードが書いてあります。
        self.tenki_data = requests.get(self.url, params=self.payload).json()
        self.oldGetTime = datetime.datetime.now()
        self.printWeather()
    
    def update(self):
        if datetime.datetime.now() - self.oldGetTime >= datetime.timedelta(days=1):
            self.tenki_data = requests.get(self.url, params=self.payload).json()
            self.oldGetTime = datetime.datetime.now()
            print("Weather Update")
            self.printWeather()
    
    def printWeather(self):
        print(self.tenki_data["title"])
        print(self.tenki_data["forecasts"][0]["date"])
        print(self.tenki_data["forecasts"][0]["telop"])
        print(self.tenki_data["forecasts"][0]["temperature"]["max"]["celsius"] if self.tenki_data["forecasts"][0]["temperature"]["max"] != None else "None")
        print(self.tenki_data["forecasts"][0]["temperature"]["min"]["celsius"] if self.tenki_data["forecasts"][0]["temperature"]["min"] != None else "None")
        print(self.tenki_data["publicTime"])

    def dumpTenkiDict(self):
        with open("./tenkiData.json","w",encoding="utf-8") as tenki:
            json.dump(self.tenki_data,tenki)
myWeather = Weather()
myWeather.update()
myWeather.dumpTenkiDict()
#秒より下の数字はいらないので必要な部分のみを取り出すための正規表現のパターン
pattern = r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}" 

#俺的曜日表現
weekDayConvList = ["GETU","KA","SUI","MOKU","KIN","DOU","NITI"]

#俺的天気表現
weatherTelopDict = {"晴れ":"HARE\n","曇り":"KUMORI\n","雨":"AME\n","曇のち雨":"KUMO->AME\n","雨時々曇":"AME<->KUMO","晴時々曇":"HARE<>KUMO"}

#シリアルポートオープン
with serial.Serial('COM3',9600,timeout=1) as ser:
    oldDatetime = re.match(pattern,str(datetime.datetime.now())).group() #前の時刻
    while True:
        newDatetime = re.match(pattern,str(datetime.datetime.now())).group() #新しい時刻
        if newDatetime != oldDatetime: #意味的には一秒以上の変化があったとき、やってることは異なるか比較している
            oldDatetime = newDatetime #前の時刻を更新
            weekDayInt = datetime.datetime.now().weekday() #曜日取得
            weatherTelop = ""
            try:
                weatherTelop = weatherTelopDict[myWeather.tenki_data["forecasts"][0]["telop"]]
            except KeyError:
                weatherTelop = "Unknown"
            #ここで実際に送信する文字列を組み立てる。年-月-日 (曜日) 時:分:秒 のフォーマット
            sendStr = \
                "\n"+ weatherTelop +"MAX:" + \
                (myWeather.tenki_data["forecasts"][0]["temperature"]["max"]["celsius"] + "\'C" if myWeather.tenki_data["forecasts"][0]["temperature"]["max"] != None else "None") +"\nMIN:" + \
                (myWeather.tenki_data["forecasts"][0]["temperature"]["min"]["celsius"] + "\'C" if myWeather.tenki_data["forecasts"][0]["temperature"]["min"] != None else "None") + "\n" + \
                "" + re.search(r"\d{4}.\d{2}.\d{2}",newDatetime).group() +\
                "(" + weekDayConvList[weekDayInt] + ")" + "\n" + \
                re.search(r"\d{2}:\d{2}",newDatetime).group()
                
            print(sendStr) #念のために表示
            flag=bytes(sendStr,'utf-8') #バイト型に変換
            try:
                ser.write(flag) #送信
            
            #よくわからんが何かシリアル通信で例外が発生したら、メッセージ表示して終了
            except serial.serialutil.SerialException:
                print("Arduinoとの接続を確認してください。")
                input()
            
            myWeather.update()

            #シリアル通信:送信
        time.sleep(1) #このループを0.1秒間隔で行う
    ser.close()
    