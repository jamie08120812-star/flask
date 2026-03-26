from flask import Flask, render_template, request

from datetime import datetime 

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>黃盈箏Python網頁20260326</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>顯示日期時間</a><hr>"
    link += "<a href=/welcome?u=盈箏&d=靜宜資管&c=資訊管理導論>GET傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/jamie>次方與根號計算</a><hr>"

    return link

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html",datetime = str(now))

@app.route("/me")
def me():
    return render_template("about資管2B黃盈箏03.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    u = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = u, dep = d,course = c)

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
