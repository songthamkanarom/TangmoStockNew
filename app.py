from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/fetch-news', methods=['POST'])
def fetch_news():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    for symbol in symbols:
        try:
            # ตัด prefix เช่น NASDAQ:, NYSE: ออก เหลือแค่ชื่อย่อหลักส่งให้ yfinance
            clean_symbol = symbol.split(":")[-1].strip()
            ticker = yf.Ticker(clean_symbol)
            
            news_list = []
            try:
                raw_news = ticker.news
                if raw_news and isinstance(raw_news, list):
                    for item in raw_news[:3]:
                        content = item.get('content', {})
                        title = content.get('title') or item.get('title')
                        
                        click_through = content.get('clickThroughUrl', {})
                        link = click_through.get('url') if isinstance(click_through, dict) else None
                        if not link:
                            link = item.get('link')
                            
                        if title and link:
                            safe_title = str(title).replace('"', '').replace("'", "").strip()
                            # จัดรูปแบบหัวข้อและลิงก์
                            news_list.append(f"• {safe_title}\n  ลิงก์ข่าว: {link}")
            except Exception:
                pass
            
            # หากไม่มีข่าวสด ให้ใช้ลิงก์สำรองหน้าหลักของ Yahoo Finance
            if not news_list:
                fallback_link = f"https://finance.yahoo.com/quote/{clean_symbol}"
                news_list.append(f"• ข้อมูลภาพรวมและสถิติของ {clean_symbol}\n  ลิงก์: {fallback_link}")
                news_list.append(f"• กราฟราคาและแนวโน้ม: {fallback_link}/chart/")
            
            news_formatted = "\n\n".join(news_list)
            results[symbol] = {"news": news_formatted}
        except Exception as e:
            results[symbol] = {"news": f"• ไม่พบข้อมูลข่าวสำหรับ {symbol}"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
