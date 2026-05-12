import os
import threading
import time
import logging
from flask import Flask, render_template, jsonify
from scraper import init_db, scrape_all, update_prices_only, get_trending, get_last_scraped, get_post_details

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

SCRAPE_INTERVAL = 3600   # 1 hour full scrape
PRICE_INTERVAL = 1800    # 30 min price refresh


def background_worker():
    while True:
        try:
            scrape_all()
        except Exception as e:
            logger.error(f"Scrape error: {e}")
        time.sleep(SCRAPE_INTERVAL)


def price_worker():
    # Wait 5 min after startup, then refresh prices every 30 min
    time.sleep(300)
    while True:
        try:
            update_prices_only()
        except Exception as e:
            logger.error(f"Price update error: {e}")
        time.sleep(PRICE_INTERVAL)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/trending')
def api_trending():
    data = get_trending(limit=30)
    last_scraped = get_last_scraped()
    return jsonify({
        'assets': data,
        'last_scraped': last_scraped,
        'count': len(data),
    })


@app.route('/api/details/<ticker>')
def api_details(ticker):
    posts = get_post_details(ticker)
    return jsonify({'ticker': ticker.upper(), 'posts': posts})


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


# Initialize on import so gunicorn picks it up too
init_db()
t = threading.Thread(target=background_worker, daemon=True)
t.start()
t2 = threading.Thread(target=price_worker, daemon=True)
t2.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
