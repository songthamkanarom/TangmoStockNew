from flask import Flask, request, jsonify
import os
import yfinance as yf
import ta
import pandas as pd
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ตั้งค่า Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# ==========================================
# ฟังก์ชันที่ 1: คำนวณ RSI, Stoch และดึงลิงก์ข่าวภาษาอังกฤษ
# ==========================================
@app.route('/calculate-indicators', methods=['POST'])
def calculate_indicators():
    data = request.json
    symbols = data.get("symbols", [])
    results = {}
    
    for symbol in symbols:
        try:
            clean_symbol = symbol.split(":")[-1].strip()
            ticker = yf.Ticker(clean_symbol)
            df = ticker.history(period="60d")
            
            if df.empty or len(df) < 15:
                results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
                continue
                
            close_prices = df['Close']
            high_prices = df['High']
            low_prices = df['Low']
            
            rsi_series = ta.momentum.rsi(close_prices, window=14)
            rsi_val = rsi_series.iloc[-1]
            current_rsi = round(float(rsi_val), 2) if not pd.isna(rsi_val) else "-"
            
            stoch_series = ta.momentum.stoch(high_prices, low_prices, close_prices, window=14, smooth_window=3)
            stoch_val = stoch_series.iloc[-1]
            current_stoch = round(float(stoch_val), 2) if not pd.isna(stoch_val) else "-"
            
            news_formatted = "-"
            try:
                raw_news = getattr(ticker, 'news', [])
                if raw_news:
                    news_items = []
                    count = 0
                    for item in raw_news:
                        if count >= 3: break
                        content = item.get('content', {}) if isinstance(item.get('content'), dict) else item
                        title = content.get('title') or item.get('title', '')
                        
                        click_through_url = content.get('clickThroughUrl') or content.get('url') or item.get('link', {})
                        if isinstance(click_through_url, dict):
                            link = click_through_url.get('url', '')
                        else:
                            link = str(click_through_url)
                            
                        if title and link and link != '-':
                            news_items.append(f"- {title} | Link: {link}")
                            count += 1
                    
                    if news_items:
                        news_formatted = "\n".join(news_items)
            except Exception:
                pass
                
            results[symbol] = {"rsi": current_rsi, "stoch": current_stoch, "news": news_formatted}
        except Exception:
            results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
            
    return jsonify({"status": "success", "data": results})

# ==========================================
# ฟังก์ชันที่ 2: อ่าน URL แล้วใช้ Gemini สรุปเป็นภาษาไทย
# ==========================================
@app.route('/summarize-news', methods=['POST'])
def summarize_news():
    data = request.json
    urls = data.get("urls", [])
    
    if not urls:
        return jsonify({"status": "error", "message": "No URLs provided"})
    
    if not api_key:
        return jsonify({"status": "error", "message": "Gemini API Key not configured"})
    
    combined_content = []
    for u in urls:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(u, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                paragraphs = [p.get_text() for p in soup.find_all('p')]
                text_snippet = " ".join(paragraphs)[:1500]
                combined_content.append(f"URL: {u}\nContent: {text_snippet}")
            else:
                combined_content.append(f"URL: {u}\n(ไม่สามารถดึงข้อความจากเว็บนี้ได้)")
        except Exception as e:
            combined_content.append(f"URL: {u}\n(Error: {str(e)})")
            
    prompt = (
        "โปรดอ่านและสรุปประเด็นสำคัญจากเนื้อหาข่าวหุ้นเหล่านี้เป็นภาษาไทยอย่างกระชับและเข้าใจง่าย "
        "จัดรูปแบบเป็นหัวข้อย่อยพร้อมระบุสาระสำคัญ:\n\n" + "\n\n".join(combined_content)
    )
    
    try:
        # ใช้ gemini-pro เพื่อให้ชัวร์ว่าไม่ติด 404
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        summary = response.text.strip()
        return jsonify({"status": "success", "summary": summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
