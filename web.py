from flask import Flask, render_template, request, make_response, jsonify
from datetime import datetime 
from google import genai
from google.genai import types
import os
import json
import firebase_admin 
from firebase_admin import credentials, firestore
import requests  
from bs4 import BeautifulSoup 
import urllib3

# 隱藏 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- 初始化區 ---
# Firebase 初始化
if not firebase_admin._apps:
    try:
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
        else:
            cred_dict = json.loads(os.getenv('FIREBASE_CONFIG'))
            cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase 初始化失敗: {e}")

# Gemini Client 初始化 (請確保環境變數 GOOGLE_API_KEY 已設定)
client = genai.Client()

# --- 路由與邏輯 ---

@app.route("/")
def index():
    return "<h1>黃盈箏Python網頁20260409</h1><a href=/webhook>聊天機器人</a>"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(force=True)
        query_result = req.get("queryResult", {})
        action = query_result.get("action", "")
        user_query = query_result.get("queryText", "")
        
        info = ""

        # 處理 AI 對話
        if action == "input.unknown":
            instruction_text = (
                "你是一個熱心且專業的智慧助理，你的開發者是黃盈箏。"
                "請用親切的口吻回答，並在回答中提到你是黃盈箏開發的助手。"
                "回覆重點，不要重述問題。"
            )
            ai_config = types.GenerateContentConfig(
                max_output_tokens=500, 
                system_instruction=instruction_text
            )
            try:
                response = client.models.generate_content(
                    model='gemini-3.5-flash', 
                    contents=user_query,
                    config=ai_config,
                )
                info = response.text
            except Exception as e:
                info = f"AI 服務暫時無法回應: {str(e)}"

        # 處理電影分級查詢
        elif action == "rateChoice":
            rate = query_result.get("parameters", {}).get("rate", "")
            info = f"我是黃盈箏開發的助手，您選擇的分級是：{rate}，相關電影：\n"
            db = firestore.client()
            docs = db.collection("本週新片含分級").get()
            
            result = ""
            for doc in docs:
                data = doc.to_dict()
                if "rate" in data and rate in data["rate"]:
                    result += f"片名：{data['title']}\n介紹：{data['hyperlink']}\n\n"
            
            info += result if result else "抱歉，找不到該分級電影。"

        return make_response(jsonify({"fulfillmentText": info}))
    
    except Exception as e:
        return make_response(jsonify({"fulfillmentText": "系統發生錯誤，請稍後再試。" + str(e)}))

# --- 其他路由保持您原有的功能 ---
# ... (建議將您的其他路由功能保留在此處)

if __name__ == "__main__":
    app.run(debug=True)