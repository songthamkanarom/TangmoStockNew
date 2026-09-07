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
                raw_news = ticker.news
                if raw_news:
                    count = 0
                    for item in raw_news:
                        if count >= 3:
                            break
                        title = item.get('title', '')
                        link = item.get('link', '')
                        if title and link:
                            news_links.append(f"• {title}\n  🔗 {link}")
                            count += 1
            except Exception:
                pass
                
            results[symbol] = {
                "news": "\n\n".join(news_links) if news_links else "-"
            }
        except Exception:
            results[symbol] = {"news": "-"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
