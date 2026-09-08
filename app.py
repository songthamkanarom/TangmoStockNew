from flask import Flask, request, jsonify
import os
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    pass

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
                # ตัดข้อความให้สั้นลงเพื่อไม่ให้เกินโควต้าการอ่าน
                text_snippet = " ".join(paragraphs)[:1500]
                combined_content.append(f"URL: {u}\nContent: {text_snippet}")
            else:
                combined_content.append(f"URL: {u}\n(ไม่สามารถดึงข้อความจากเว็บนี้ได้โดยตรง)")
        except Exception as e:
            combined_content.append(f"URL: {u}\n(Error: {str(e)})")
            
    prompt = (
        "โปรดอ่านและสรุปประเด็นสำคัญจากเนื้อหาข่าวหุ้นเหล่านี้เป็นภาษาไทยอย่างกระชับและเข้าใจง่าย "
        "จัดรูปแบบเป็นหัวข้อย่อยพร้อมระบุสาระสำคัญ:\n\n" + "\n\n".join(combined_content)
    )
    
    try:
        # เปลี่ยนมาใช้ gemini-pro ซึ่งรองรับแน่นอน 100%
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        summary = response.text.strip()
        return jsonify({"status": "success", "summary": summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
