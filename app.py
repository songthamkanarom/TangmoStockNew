from flask import Flask, request, jsonify
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

app = Flask(__name__)

@app.route('/fetch-news', methods=['POST'])
def fetch_news():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    translator = GoogleTranslator(source='auto', target='th')
    
    for symbol in symbols:
        try:
            clean_symbol = symbol.split(":")[-1].strip()
            ticker = yf.Ticker(clean_symbol)
            
            news_list = []
            try:
                raw_news = ticker.news
                if raw_news and isinstance(raw_news, list):
                    # ดึงมา 2 ข่าวแรกเพื่อไม่ให้ข้อมูลยาวเกินไปและป้องกันเวลาประมวลผลนานเกิน
                    for item in raw_news[:2]:
                        content = item.get('content', {})
                        title = content.get('title') or item.get('title')
                        
                        click_through = content.get('clickThroughUrl', {})
                        link = click_through.get('url') if isinstance(click_through, dict) else None
                        if not link:
                            link = item.get('link')
                            
                        if title and link:
                            safe_title = str(title).replace('"', '').replace("'", "").strip()
                            
                            # 1. แปลหัวข้อข่าวเป็นไทย
                            try:
                                thai_title = translator.translate(safe_title)
                            except:
                                thai_title = safe_title
                            
                            # 2. เปิดเข้าไปอ่านเนื้อหาข้างในลิงก์ (Scrape Web Content)
                            article_summary = "ไม่สามารถดึงเนื้อหาฉบับเต็มได้"
                            try:
                                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                                resp = requests.get(link, headers=headers, timeout=5)
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    # ดึงย่อหน้าเนื้อหาจากเว็บข่าว
                                    paragraphs = soup.find_all('p')
                                    text_content = " ".join([p.get_text() for p in paragraphs[:6]]) # ดึง 6 ย่อหน้าแรก
                                    
                                    if text_content.strip():
                                        # แปลเนื้อหาเป็นไทย (จำกัดความยาวไม่ให้เกิน 1,500 ตัวอักษรต่อข่าวเพื่อความเสถียร)
                                        translated_text = translator.translate(text_content[:1500])
                                        article_summary = translated_text
                            except Exception as e:
                                article_summary = "เนื้อหาถูกจำกัดการเข้าถึงหรือโหลดไม่ทัน"
                            
                            news_list.append(f"• หัวข้อ: {thai_title}\n\nเนื้อหาสรุปภาษาไทย:\n{article_summary}\n\n🔗 ลิงก์ข่าวต้นฉบับ: {link}")
            except Exception as e:
                pass
            
            if not news_list:
                fallback_link = f"https://finance.yahoo.com/quote/{clean_symbol}"
                news_list.append(f"• ข้อมูลภาพรวมและสถิติของ {clean_symbol}\n  ลิงก์: {fallback_link}")
            
            news_formatted = "\n\n" + "="*30 + "\n\n".join(news_list)
            results[symbol] = {"news": news_formatted}
        except Exception as e:
            results[symbol] = {"news": f"• ไม่พบข้อมูลข่าวสำหรับ {symbol}"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
