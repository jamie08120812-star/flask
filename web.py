from flask import Flask, render_template, request
from datetime import datetime 
import os
import json
import firebase_admin 
from firebase_admin import credentials, firestore
import requests  # 移到最上方
from bs4 import BeautifulSoup # 移到最上方
import urllib3

# 隱藏 SSL 警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Firebase 初始化
if os.path.exists('serviceAccountKey.json'):
    # 本地環境
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境（例如 Vercel）
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
    link += "<br><a href=/spiter>爬取資料</a><br>"
    link += "<br><a href=/movie1>爬取即將上映電影</a><br>"
    return link

@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
   

    R = """
    <form action="/movie1" method="get">
        <label>請輸入電影關鍵字：</label>
        <input type="text" name="keyword" value="{}">
        <button type="submit">搜尋</button>
    </form>
    <hr>
    """.format(keyword)
   
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

@app.route("/spiter")
def spiter():
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    try:
        # verify=False 跳過 SSL 檢查
        Data = requests.get(url, verify=False)
        Data.encoding = "utf-8"
        
        sp = BeautifulSoup(Data.text, "html.parser")
        items = sp.select(".team-box a")

        info = "<h3>課程資料：</h3>" 
        for i in items:
            info += i.text + " ( " + i.get("href") + " )<br>"
        
        return info
    except Exception as e:
        return f"抓取失敗，錯誤原因：{str(e)}"

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
        Result += f"<h3>查詢結果 (關鍵字: {keyword}):</h3>"
        
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
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/jamie")
def jamie():
    return render_template("jamie.html")

if __name__ == "__main__":
    app.run(debug=True)