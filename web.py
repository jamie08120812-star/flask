from flask import Flask, render_template, request
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

    return link

@app.route("/spitermo")
def spitermo():
    R = ""
    db = firestore.client()
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間:","")
    result=sp.select(".filmListAllX li")
    total = 0
    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/","").replace("/","")
      title = item.find(class_="filmtitle").text
      picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
      showDate = item.find(class_="runtime").text[5:15]

      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "lastUpdate": lastUpdate
      }
      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

    R += "網站最新更新日期:" + lastUpdate + "<br>" 
    R += "總共爬取" + str(total) + "部電影到資料庫"
    return R

@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
    R = f"""
    <form action="/movie1" method="get">
        <label>請輸入電影關鍵字：</label>
        <input type="text" name="keyword" value="{keyword}">
        <button type="submit">搜尋</button>
    </form>
    <hr>
    """
    if keyword:
        R += "您搜尋的關鍵字是：<b>" + keyword + "</b><br><br>"
   
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
            R += "<b>" + title + "</b><br>"
            R += '<a href="' + introduce + '" target="_blank">介紹頁超鏈結</a><br>'
            R += '<img src="' + img_url + '" width="200"><br><br>'
    return R

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()     
    for doc in docs:          
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/read2", methods=["GET", "POST"])
def read2():
    Result = "<h1>靜宜資管老師查詢</h1>"
    Result += '<form action="/read2" method="post">'
    Result += '請輸入老師姓名關鍵字：<input type="text" name="keyword">'
    Result += '<button type="submit">查詢</button></form><br>'

    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        found = False
        for doc in docs:
            teacher_data = doc.to_dict()
            name = teacher_data.get('name')
            if name and keyword in name:
                found = True
                lab = teacher_data.get('lab', '未知')
                Result += f"<span style='color:blue; font-weight:bold'>{name}</span> 老師的研究室是在 <b>{lab}</b><br>"
        if not found:
            Result += f"找不到姓名包含「{keyword}」的老師。<br>"
    Result += "<br><a href=/>返回首頁</a>"
    return Result

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
    u = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = u, dep = d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
    else:
        return render_template("account.html")

@app.route("/jamie")
def jamie():
    return render_template("jamie.html")

@app.route("/searchQ", methods=["POST", "GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""
        db = firestore.client()
        collection_ref = db.collection("電影2B")
        docs = collection_ref.order_by("showDate").get()
        for doc in docs:
            movie_data = doc.to_dict()
            if MovieTitle in movie_data.get("title", ""):
                info += "片名：" + movie_data.get("title", "") + "<br>"
                
                # 圖片顯示
                picture_url = movie_data.get("picture", "")
                if picture_url:
                    info += f"<img src='{picture_url}' width='150'><br>"
                
                # 修改為可點擊的超連結
                hyperlink = movie_data.get("hyperlink", "")
                info += f"影片介紹：<a href='{hyperlink}' target='_blank'>介紹頁超連結</a><br>"
                
                info += "片長：" + str(movie_data.get("showLength", "未提供")) + " 分鐘<br>"
                info += "上映日期：" + movie_data.get("showDate", "") + "<br><hr>"
        return info
    else:
        return render_template("input.html")

if __name__ == "__main__":
    app.run(debug=True)