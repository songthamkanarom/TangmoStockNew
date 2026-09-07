from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/fetch-news-links', methods=['POST'])
def fetch_news_links():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    for symbol in symbols:
        try:
            clean_symbol = symbol.split(":")[-1].strip()
            ticker = yf.Ticker(clean_symbol)
            
            news_links = []
            try:
                # รองรับทั้งฟังก์ชัน .news ปกติและ .get_news() ใน yfinance หลายเวอร์ชัน
                raw_news = []
                if hasattr(ticker, "get_news"):
                    raw_news = ticker.get_news()
                elif hasattr(ticker, "news"):
                    raw_news = ticker.news
                
                if raw_news:
                    count = 0
                    for item in raw_news:
                        if count >= 3:
                            break
                        
                        # ดึงข้อมูลจากโครงสร้างที่อาจจะอยู่ใน content หรือ level ปกติ
                        title = ""
                        link = ""
                        
                        if isinstance(item, dict):
                            # รูปแบบมาตรฐานทั่วไป
                            title = item.get('title', '')
                            link = item.get('link', '')
                            
                            # รูปแบบโครงสร้างใหม่บางเวอร์ชัน (nested under content)
                            if not title and 'content' in item:
                                content = item.get('content', {})
                                title = content.get('title', '')
                                if 'clickThroughUrl' in content and content['clickThroughUrl']:
                                    link = content['clickThroughUrl'].get('url', '')
                            
                            # ถ้ายังไม่มี link ให้ลองหาฟิลด์สำรอง
                            if not link and 'providerPublishTime' in item:
                                pass # ข้ามถ้าไม่มีลิงก์จริง
                                
                        if title and link:
                            news_links.append(f"• {title}\n  🔗 {link}")
                            count += 1
            except Exception as e:
                print(f"Error fetching news for {symbol}: {str(e)}")
                
            results[symbol] = {
                "news": "\n\n".join(news_links) if news_links else "• ไม่พบข่าวสารล่าสุดหรือลิงก์อ้างอิงจาก Yahoo Finance ในขณะนี้"
            }
        except Exception as e:
            results[symbol] = {"news": "• เกิดข้อผิดพลาดในการเชื่อมต่อข้อมูลหุ้น"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='
