from flask import Flask, request, jsonify
import yfinance as yf
import ta
import pandas as pd

app = Flask(__name__)

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
            
            # ดึงข่าวสารล่าสุด 3 ลิงก์ (ปรับปรุงการดึงข้อมูลให้ครอบคลุมยิ่งขึ้น)
            news_formatted = "-"
            try:
                raw_news = getattr(ticker, 'news', None)
                if not raw_news:
                    # ลองดึงผ่านฟังก์ชันสำรองหากมี
                    raw_news = []
                
                if raw_news:
                    news_items = []
                    count = 0
                    for item in raw_news:
                        if count >= 3:
                            break
                        # รองรับโครงสร้างข้อมูลข่าวหลายรูปแบบของ yfinance
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
            except Exception as e:
                print(f"News error for {clean_symbol}: {e}")
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
