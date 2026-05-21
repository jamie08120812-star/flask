from flask import Flask, render_template, request,make_response, jsonify
from datetime import datetime 

import os
import json
import firebase_admin 
from firebase_admin import credentials, firestore
import requests  
from bs4 import BeautifulSoup 
import urllib3

# 隱藏 SSL 警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Firebase 初始化
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG 沒有設定")
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

# --- 路由定義開始 ---

@app.route("/")
def index():
    link = "<h1>黃盈箏Python網頁20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>顯示日期時間</a><hr>"
    link += "<a href=/welcome?u=盈箏&d=靜宜資管&c=資訊管理導論>GET傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/jamie>次方與根號計算</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read2>讀取姓名資料</a><br>"
    link += "<br><a href=/spider>爬取資料</a><br>"
    link += "<br><a href=/movie1>搜尋即將上映電影</a><br>"
    link += "<br><a href=/spitermo>爬取即將上映電影</a><br>"
    link += "<br><a href=/searchQ>查詢電影 (Firestore)</a><br>" 
    link += "<br><a href=/road>台中市十大肇事路口</a><br>" 
    link += "<br><a href=/weather>天氣</a><br>" 
    link += "<br><a href=/rate>爬取開眼電影資訊 </a><br>" 
    link += "<br><a href=/webdemo>聊天機器人 </a><br>" 
    return link



@app.route("/webdemo")
def webdemo():
    return render_template("webdemo.html")



@app.route("/webhook", methods=["POST"])
def webhook3():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req["queryResult"]["action"]
    #msg =  req.get("queryResult").get("queryText")
    #info = "動作：" + action + "； 查詢內容：" + msg
    if (action == "rateChoice"):
        rate =  req["queryResult"]["parameters"]["rate"]
        info = "我是黃營箏開發的電影聊天機器人,您選擇的電影分級是：" + rate + "，相關電影：\n"
    db = firestore.client()
        # 注意：這裡要改成你截圖中真實的集合名稱
    collection_ref = db.collection("本週新片含分級")
    docs = collection_ref.get()
       
    result = ""
        # 2. 迴圈讀取每一筆電影資料
    for doc in docs:
        doc_dict = doc.to_dict()
           
            # 先確認字典裡有 'rate' 這個鍵，避免發生 KeyError 報錯
            # 再檢查使用者要找的分級 (rate) 有沒有包含在資料庫的 'rate' 欄位裡
        if "rate" in doc_dict and rate in doc_dict["rate"]:
            result += "片名：" + doc_dict["title"] + "\n"
            result += "介紹：" + doc_dict["hyperlink"] + "\n\n"
       
        # 3. 判斷是否有找到資料
    if result == "":
        info += "抱歉，目前資料庫中沒有找到這個分級的電影喔！"
    else:
        info += result
    return make_response(jsonify({"fulfillmentText": info}))



@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


@app.route("/weather")
def weather():
    city = request.args.get("city")
    if not city:
        return '''
            <h2>氣象查詢系統</h2>
            <form action="/weather" method="GET">
                請輸入縣市 (例如：臺中市)：<input type="text" name="city" required>
                <input type="submit" value="查詢">
            </form>
        '''
    city_formatted = city.replace("台", "臺")
    token = "rdec-key-123-45678-011121314"
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city_formatted}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        Data = requests.get(url, headers=headers, verify=False, timeout=10)
        if Data.status_code == 200:
            json_data = json.loads(Data.text)
            location_data = json_data["records"]["location"][0]
            weather_status = location_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
            rain_prob = location_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
            return f'''
                <h2>查詢結果：{city_formatted}</h2>
                <p>目前天氣：{weather_status}</p>
                <p>降雨機率：{rain_prob}%</p>
                <br><br><a href="/weather">返回重新查詢</a>
            '''
        else:
            return f"無法取得資料，錯誤代碼：{Data.status_code}"
    except Exception as e:
        return f"連線發生錯誤：{e}"

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者:黃盈箏</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        Data = requests.get(url, headers=headers, verify=False, timeout=10)
        Data.encoding = 'utf-8'
        JsonData = json.loads(Data.text)
        Result = ""
        for item in JsonData:
            Result += f"{item['路口名稱']} : 發生 {item['總件數']} 件，主因是 {item['主要肇因']}\n"
        return R + Result.replace("\n", "<br>")
    except Exception as e:
        return f"發生錯誤：{e}"

@app.route("/spitermo")
def spitermo():
    db = firestore.client()
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間:","")
    result = sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1
        movie_id = item.find("a").get("href").replace("/movie/","").replace("/","")
        title = item.find(class_="filmtitle").text
        picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
        showDate = item.find(class_="runtime").text[5:15]
        doc = {"title": title, "picture": picture, "hyperlink": hyperlink, "showDate": showDate, "lastUpdate": lastUpdate}
        db.collection("電影2B").document(movie_id).set(doc)
    return f"網站最新更新日期:{lastUpdate}<br>總共爬取{total}部電影到資料庫"

@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
    R = f'<form action="/movie1" method="get">請輸入電影關鍵字：<input type="text" name="keyword" value="{keyword}"><button type="submit">搜尋</button></form><hr>'
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    for item in result:
        title = item.find("img").get("alt")
        if not keyword or keyword in title:
            introduce = "https://www.atmovies.com.tw" + item.find("a").get("href")
            img_url = "https://www.atmovies.com.tw" + item.find("img").get("src")
            R += f"<b>{title}</b><br><a href='{introduce}' target='_blank'>介紹頁超鏈結</a><br><img src='{img_url}' width='200'><br><br>"
    return R

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    docs = db.collection("靜宜資管").get()     
    for doc in docs: Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/read2", methods=["GET", "POST"])
def read2():
    Result = "<h1>靜宜資管老師查詢</h1><form action='/read2' method='post'>請輸入老師姓名關鍵字：<input type='text' name='keyword'><button type='submit'>查詢</button></form><br>"
    if request.method == "POST":
        keyword = request.form.get("keyword")
        docs = firestore.client().collection("靜宜資管").get()
        for doc in docs:
            teacher_data = doc.to_dict()
            name = teacher_data.get('name')
            if name and keyword in name:
                Result += f"<span style='color:blue; font-weight:bold'>{name}</span> 老師的研究室是在 <b>{teacher_data.get('lab', '未知')}</b><br>"
    return Result + "<br><a href=/>返回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    return render_template("about資管2B黃盈箏03.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    u, d, c = request.values.get("u"), request.values.get("d"), request.values.get("c")
    return render_template("welcome.html", name = u, dep = d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        return f"您輸入的帳號是：{request.form['user']}; 密碼為：{request.form['pwd']}"
    return render_template("account.html")

@app.route("/jamie")
def jamie():
    return render_template("jamie.html")

@app.route("/searchQ", methods=["POST", "GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""
        docs = firestore.client().collection("電影2B").order_by("showDate").get()
        for doc in docs:
            movie_data = doc.to_dict()
            if MovieTitle in movie_data.get("title", ""):
                info += f"片名：{movie_data.get('title')}<br><img src='{movie_data.get('picture')}' width='150'><br>影片介紹：<a href='{movie_data.get('hyperlink')}' target='_blank'>介紹頁超連結</a><br>上映日期：{movie_data.get('showDate')}<br><hr>"
        return info
    return render_template("input.html")

# --- 啟動伺服器 (務必放在檔案最末端) ---
if __name__ == "__main__":
    app.run(debug=True)