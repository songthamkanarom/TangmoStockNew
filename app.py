from flask import Flask, request, jsonify
import yfinance as yf
import ta
import pandas as pd
import os
import google.generativeai as genai

app = Flask(__name__)

# ตั้งค่า Gemini API จาก Environment Variable บน Render
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    generation_config = {
        "temperature": 0.3,
        "max_output_tokens": 500,
    }
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
else:
    model = None

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
            
            # คำนวณ RSI (14)
            rsi_series = ta.momentum.rsi(close_prices, window=14)
            rsi_val = rsi_series.iloc[-1]
            current_rsi = round(float(rsi_val), 2) if not pd.isna(rsi_val) else "-"
            
            # คำนวณ Stochastic %K (14, 3)
            stoch_series = ta.momentum.stoch(high_prices, low_prices, close_prices, window=14, smooth_window=3)
            stoch_val = stoch_series.iloc[-1]
            current_stoch = round(float(stoch_val), 2) if not pd.isna(stoch_val) else "-"
            
            # ดึงข่าวสารล่าสุดและแปลเป็นไทยผ่าน Gemini
            news_formatted = "-"
            try:
                raw_news = ticker.news
                if raw_news and model:
                    news_items = []
                    count = 0
                    for item in raw_news:
                        if count >= 3:
                            break
                        title = item.get('title', '')
                        link = item.get('link', '')
                        if title and link:
                            news_items.append(f"- {title} | Link: {link}")
                            count += 1
                    
                    if news_items:
                        prompt = (
                            f"Translate the following stock news titles into natural Thai. "
                            f"Keep the exact link provided for each item. Format as bullet points "
                            f"with the Thai translated title followed by the link in parentheses:\n\n" + 
                            "\n".join(news_items)
                        )
                        response = model.generate_content(prompt)
                        news_formatted = response.text.strip()
            except Exception:
                pass
                
            results[symbol] = {
                "rsi": current_rsi,
                "stoch": current_stoch,
                "news": news_formatted
            }
        except Exception as e:
            results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
