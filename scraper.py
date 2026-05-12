import requests
import re
import sqlite3
import time
import os
import logging
import yfinance as yf
from datetime import datetime, timedelta
from collections import Counter, defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

SUBREDDITS = [
    'wallstreetbets', 'stocks', 'investing', 'StockMarket',
    'options', 'pennystocks', 'Daytrading',
    'CryptoCurrency', 'Bitcoin', 'ethereum', 'CryptoMarkets', 'solana',
]

STOCK_TICKERS = {
    'AAPL': 'Apple', 'TSLA': 'Tesla', 'NVDA': 'NVIDIA', 'MSFT': 'Microsoft',
    'AMZN': 'Amazon', 'GOOGL': 'Alphabet', 'GOOG': 'Alphabet', 'META': 'Meta',
    'AMD': 'AMD', 'GME': 'GameStop', 'AMC': 'AMC', 'PLTR': 'Palantir',
    'RIVN': 'Rivian', 'LCID': 'Lucid Motors', 'F': 'Ford', 'GM': 'General Motors',
    'BABA': 'Alibaba', 'NIO': 'NIO', 'SOFI': 'SoFi', 'HOOD': 'Robinhood',
    'COIN': 'Coinbase', 'MARA': 'Marathon Digital', 'RIOT': 'Riot Platforms',
    'MSTR': 'MicroStrategy', 'CLSK': 'CleanSpark', 'SPY': 'S&P 500 ETF',
    'QQQ': 'Nasdaq ETF', 'IWM': 'Russell 2000 ETF', 'VOO': 'Vanguard S&P500',
    'ARKK': 'ARK Innovation', 'INTC': 'Intel', 'QCOM': 'Qualcomm', 'MU': 'Micron',
    'SMCI': 'Super Micro', 'ARM': 'ARM Holdings', 'AVGO': 'Broadcom',
    'TSM': 'TSMC', 'ASML': 'ASML', 'NFLX': 'Netflix', 'DIS': 'Disney',
    'UBER': 'Uber', 'LYFT': 'Lyft', 'SNAP': 'Snapchat', 'PINS': 'Pinterest',
    'SHOP': 'Shopify', 'SQ': 'Block', 'PYPL': 'PayPal', 'V': 'Visa',
    'MA': 'Mastercard', 'JPM': 'JPMorgan', 'BAC': 'Bank of America',
    'WFC': 'Wells Fargo', 'GS': 'Goldman Sachs', 'MS': 'Morgan Stanley',
    'XOM': 'ExxonMobil', 'CVX': 'Chevron', 'OXY': 'Occidental',
    'NEE': 'NextEra Energy', 'ENPH': 'Enphase', 'FSLR': 'First Solar',
    'LI': 'Li Auto', 'XPEV': 'XPeng', 'RKLB': 'Rocket Lab',
    'IONQ': 'IonQ', 'QUBT': 'Quantum Computing', 'RGTI': 'Rigetti',
    'MELI': 'MercadoLibre', 'SE': 'Sea Limited', 'DKNG': 'DraftKings',
    'ROKU': 'Roku', 'SPOT': 'Spotify', 'ABNB': 'Airbnb', 'DASH': 'DoorDash',
    'RBLX': 'Roblox', 'U': 'Unity', 'AFRM': 'Affirm', 'UPST': 'Upstart',
    'C': 'Citigroup', 'T': 'AT&T', 'VZ': 'Verizon', 'CSCO': 'Cisco',
    'ORCL': 'Oracle', 'CRM': 'Salesforce', 'NOW': 'ServiceNow',
    'SNOW': 'Snowflake', 'DDOG': 'Datadog', 'NET': 'Cloudflare',
    'ZS': 'Zscaler', 'CRWD': 'CrowdStrike', 'PANW': 'Palo Alto',
    'OKTA': 'Okta', 'MDB': 'MongoDB', 'GTLB': 'GitLab', 'HIMS': 'Hims & Hers',
    'NVO': 'Novo Nordisk', 'LLY': 'Eli Lilly', 'PFE': 'Pfizer',
    'MRNA': 'Moderna', 'BNTX': 'BioNTech', 'NVAX': 'Novavax',
}

CRYPTO_ASSETS = {
    'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'SOL': 'Solana', 'XRP': 'XRP',
    'DOGE': 'Dogecoin', 'ADA': 'Cardano', 'MATIC': 'Polygon', 'POL': 'Polygon',
    'AVAX': 'Avalanche', 'DOT': 'Polkadot', 'LINK': 'Chainlink',
    'UNI': 'Uniswap', 'ATOM': 'Cosmos', 'LTC': 'Litecoin', 'BCH': 'Bitcoin Cash',
    'TRX': 'Tron', 'SHIB': 'Shiba Inu', 'PEPE': 'Pepe', 'WIF': 'dogwifhat',
    'BONK': 'Bonk', 'SUI': 'Sui', 'APT': 'Aptos', 'ARB': 'Arbitrum',
    'INJ': 'Injective', 'BNB': 'BNB', 'TON': 'Toncoin', 'NOT': 'Notcoin',
    'JUP': 'Jupiter', 'WLD': 'Worldcoin', 'OP': 'Optimism', 'STX': 'Stacks',
    'IMX': 'Immutable', 'NEAR': 'NEAR Protocol', 'FTM': 'Fantom',
    'SAND': 'The Sandbox', 'MANA': 'Decentraland', 'APE': 'ApeCoin',
    'LDO': 'Lido', 'RPL': 'Rocket Pool', 'AAVE': 'Aave', 'MKR': 'Maker',
    'CRV': 'Curve', 'SUSHI': 'SushiSwap', 'CAKE': 'PancakeSwap',
    'FIL': 'Filecoin', 'AR': 'Arweave', 'ICP': 'Internet Computer',
    'RENDER': 'Render', 'FET': 'Fetch.ai', 'AGIX': 'SingularityNET',
}

CRYPTO_NAMES = {
    'bitcoin': 'BTC', 'ethereum': 'ETH', 'solana': 'SOL', 'ripple': 'XRP',
    'dogecoin': 'DOGE', 'cardano': 'ADA', 'polygon': 'MATIC', 'avalanche': 'AVAX',
    'polkadot': 'DOT', 'chainlink': 'LINK', 'uniswap': 'UNI', 'cosmos': 'ATOM',
    'litecoin': 'LTC', 'shiba inu': 'SHIB', 'shiba': 'SHIB', 'pepe': 'PEPE',
    'arbitrum': 'ARB', 'optimism': 'OP', 'injective': 'INJ', 'toncoin': 'TON',
    'near protocol': 'NEAR', 'fantom': 'FTM', 'filecoin': 'FIL',
    'immutable': 'IMX', 'aptos': 'APT', 'sui': 'SUI',
}

AMBIGUOUS_TICKERS = {
    'A', 'B', 'C', 'D', 'F', 'I', 'K', 'O', 'R', 'T', 'U', 'V', 'X', 'Y',
    'IT', 'IS', 'OR', 'NO', 'ON', 'AT', 'IN', 'TO', 'BY', 'WE', 'ME',
    'US', 'HE', 'OF', 'AS', 'IF', 'MY', 'HI', 'OK', 'OH', 'AM', 'PM',
    'GO', 'UP', 'BE', 'DO', 'SO', 'TV', 'PC', 'UK', 'EU', 'OP', 'NOT',
    'NOW', 'NEW', 'ARE', 'FOR', 'ALL', 'AND', 'BUT', 'THE',
}

IGNORE_WORDS = {
    'CEO', 'IPO', 'ETF', 'SEC', 'FED', 'IMO', 'DCA', 'ATH', 'ATL', 'DD',
    'TA', 'OTC', 'EV', 'AI', 'USD', 'GDP', 'CPI', 'YOY', 'QOQ', 'MOM',
    'EOD', 'AH', 'PR', 'IR', 'HR', 'VP', 'CF', 'EPS', 'PE', 'PB',
    'ROE', 'ROI', 'YOLO', 'FOMO', 'FUD', 'HODL', 'WEN', 'GG', 'GL',
    'LOL', 'TBH', 'TLDR', 'NFA', 'IIRC', 'AFAIK', 'OMG', 'WTF',
    'EOW', 'EOY', 'IRL', 'AMA', 'IMHO', 'FYI', 'LMAO', 'ROFL',
    'SMH', 'TIL', 'DAE', 'CMV', 'ELI', 'EDIT', 'UPDATE', 'OP',
}

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sentiment.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            full_name TEXT NOT NULL,
            count INTEGER NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS top_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            title TEXT NOT NULL,
            subreddit TEXT NOT NULL,
            score INTEGER NOT NULL,
            url TEXT NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT PRIMARY KEY,
            asset_type TEXT,
            price REAL,
            change_pct REAL,
            updated_at TIMESTAMP
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ticker_time ON mentions(ticker, scraped_at)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_posts_ticker ON top_posts(ticker, scraped_at)')
    conn.commit()
    conn.close()


def extract_mentions(text):
    mentions = Counter()
    if not text:
        return mentions

    dollar_matches = re.findall(r'\$([A-Za-z]{1,6})\b', text)
    for match in dollar_matches:
        ticker = match.upper()
        if ticker in STOCK_TICKERS:
            mentions[('stock', ticker)] += 3
        elif ticker in CRYPTO_ASSETS:
            mentions[('crypto', ticker)] += 3

    words = re.findall(r'\b([A-Z]{2,6})\b', text)
    for word in words:
        if word in IGNORE_WORDS or word in AMBIGUOUS_TICKERS:
            continue
        if word in STOCK_TICKERS:
            mentions[('stock', word)] += 1
        elif word in CRYPTO_ASSETS:
            mentions[('crypto', word)] += 1

    text_lower = text.lower()
    for name, ticker in CRYPTO_NAMES.items():
        if name in text_lower:
            mentions[('crypto', ticker)] += 1

    return mentions


def fetch_subreddit(subreddit, limit=100):
    headers = {'User-Agent': 'SentimentTracker/1.0 (Educational project)'}
    posts = []
    for sort in ['hot', 'new']:
        try:
            url = f'https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}'
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get('data', {}).get('children', []):
                    d = post.get('data', {})
                    posts.append({
                        'title': d.get('title', ''),
                        'selftext': d.get('selftext', ''),
                        'score': d.get('score', 0),
                        'subreddit': subreddit,
                        'permalink': 'https://reddit.com' + d.get('permalink', ''),
                    })
            time.sleep(1.5)
        except Exception as e:
            logger.warning(f"Error fetching r/{subreddit}/{sort}: {e}")
    return posts


def fetch_apewisdom():
    """Fetch trending tickers from ApeWisdom (aggregated Reddit data)"""
    try:
        url = 'https://apewisdom.io/api/v1.0/filter/all-subreddits/page/1'
        headers = {'User-Agent': 'SentimentTracker/1.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = {}
            for item in data.get('results', []):
                ticker = item.get('ticker', '').upper()
                mentions = item.get('mentions', 0)
                if ticker and mentions:
                    results[ticker] = int(mentions)
            logger.info(f"ApeWisdom: {len(results)} tickers fetched")
            return results
    except Exception as e:
        logger.warning(f"ApeWisdom error: {e}")
    return {}


def fetch_stocktwits(tickers):
    """Fetch StockTwits mention counts and sentiment for top tickers"""
    headers = {'User-Agent': 'SentimentTracker/1.0'}
    results = {}
    for ticker in tickers[:12]:
        try:
            url = f'https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json?limit=30'
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                messages = data.get('messages', [])
                bullish = sum(1 for m in messages
                              if m.get('entities', {}).get('sentiment') and
                              m['entities']['sentiment'].get('basic') == 'Bullish')
                bearish = sum(1 for m in messages
                              if m.get('entities', {}).get('sentiment') and
                              m['entities']['sentiment'].get('basic') == 'Bearish')
                results[ticker] = {
                    'count': len(messages),
                    'bullish': bullish,
                    'bearish': bearish,
                }
            time.sleep(1.2)
        except Exception as e:
            logger.warning(f"StockTwits error for {ticker}: {e}")
    logger.info(f"StockTwits: {len(results)} tickers fetched")
    return results


def format_price(price):
    if price is None:
        return None
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    else:
        return f"${price:.6f}"


def fetch_prices(ticker_type_map):
    """Fetch current prices and daily change using yfinance"""
    prices = {}
    if not ticker_type_map:
        return prices

    stock_tickers = [t for t, typ in ticker_type_map.items() if typ == 'stock']
    crypto_tickers = [t for t, typ in ticker_type_map.items() if typ == 'crypto']

    # Fetch stocks
    if stock_tickers:
        try:
            syms = ' '.join(stock_tickers)
            data = yf.download(syms, period='2d', interval='1d',
                               progress=False, auto_adjust=True)
            close = data['Close']
            for ticker in stock_tickers:
                try:
                    series = close[ticker] if len(stock_tickers) > 1 else close
                    series = series.dropna()
                    if len(series) >= 2:
                        p = float(series.iloc[-1])
                        prev = float(series.iloc[-2])
                        change = round(((p - prev) / prev) * 100, 2)
                        prices[ticker] = {'price': p, 'price_str': format_price(p), 'change': change}
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"yfinance stocks error: {e}")

    # Fetch crypto
    if crypto_tickers:
        try:
            yf_syms = [t + '-USD' for t in crypto_tickers]
            syms = ' '.join(yf_syms)
            data = yf.download(syms, period='2d', interval='1d',
                               progress=False, auto_adjust=True)
            close = data['Close']
            for ticker in crypto_tickers:
                try:
                    yf_sym = ticker + '-USD'
                    series = close[yf_sym] if len(crypto_tickers) > 1 else close
                    series = series.dropna()
                    if len(series) >= 2:
                        p = float(series.iloc[-1])
                        prev = float(series.iloc[-2])
                        change = round(((p - prev) / prev) * 100, 2)
                        prices[ticker] = {'price': p, 'price_str': format_price(p), 'change': change}
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"yfinance crypto error: {e}")

    logger.info(f"Prices fetched: {len(prices)} tickers")
    return prices


def scrape_all():
    logger.info("Starting full scrape...")
    all_mentions = Counter()
    ticker_posts = defaultdict(list)
    ticker_types = {}

    # 1. Reddit scraping
    for subreddit in SUBREDDITS:
        posts = fetch_subreddit(subreddit)
        logger.info(f"r/{subreddit}: {len(posts)} posts")
        for post in posts:
            text = post['title'] + ' ' + post['selftext']
            mentions = extract_mentions(text)
            weight = max(1, min(5, 1 + post['score'] // 1000))
            for key, count in mentions.items():
                all_mentions[key] += count * weight
                ticker_types[key[1]] = key[0]
                ticker_posts[key[1]].append({
                    'title': post['title'][:250],
                    'subreddit': post['subreddit'],
                    'score': post['score'],
                    'url': post['permalink'],
                })

    # 2. ApeWisdom (extra Reddit aggregation)
    ape_data = fetch_apewisdom()
    for ticker, count in ape_data.items():
        if ticker in STOCK_TICKERS:
            all_mentions[('stock', ticker)] += count // 3
            ticker_types[ticker] = 'stock'
        elif ticker in CRYPTO_ASSETS:
            all_mentions[('crypto', ticker)] += count // 3
            ticker_types[ticker] = 'crypto'

    # 3. StockTwits (for top stock tickers)
    top_stocks = [k[1] for k in all_mentions if k[0] == 'stock'][:12]
    st_data = fetch_stocktwits(top_stocks)
    for ticker, data in st_data.items():
        if ticker in STOCK_TICKERS:
            all_mentions[('stock', ticker)] += data['count']

    # Save mentions to DB
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    for (asset_type, ticker), count in all_mentions.items():
        full_name = STOCK_TICKERS.get(ticker, CRYPTO_ASSETS.get(ticker, ticker))
        conn.execute(
            'INSERT INTO mentions (ticker, asset_type, full_name, count, scraped_at) VALUES (?,?,?,?,?)',
            (ticker, asset_type, full_name, count, now)
        )

    # Save top posts
    cutoff = (datetime.utcnow() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('DELETE FROM top_posts WHERE scraped_at < ?', (cutoff,))
    for ticker, posts in ticker_posts.items():
        seen = set()
        unique = []
        for p in sorted(posts, key=lambda x: x['score'], reverse=True):
            if p['title'] not in seen:
                seen.add(p['title'])
                unique.append(p)
            if len(unique) >= 5:
                break
        for p in unique:
            conn.execute(
                'INSERT INTO top_posts (ticker, title, subreddit, score, url, scraped_at) VALUES (?,?,?,?,?,?)',
                (ticker, p['title'], p['subreddit'], p['score'], p['url'], now)
            )

    conn.commit()
    conn.close()

    # 4. Fetch prices for all tracked tickers
    prices = fetch_prices(ticker_types)
    if prices:
        conn = sqlite3.connect(DB_PATH)
        for ticker, pdata in prices.items():
            conn.execute('''
                INSERT OR REPLACE INTO prices (ticker, asset_type, price, change_pct, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticker, ticker_types.get(ticker, 'stock'),
                  pdata['price'], pdata['change'], now))
        conn.commit()
        conn.close()

    logger.info(f"Scrape complete. {len(all_mentions)} assets, {len(prices)} prices.")


def get_post_details(ticker):
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        cur = conn.execute('''
            SELECT title, subreddit, score, url
            FROM top_posts
            WHERE ticker = ? AND scraped_at >= ?
            ORDER BY score DESC LIMIT 5
        ''', (ticker.upper(), cutoff))
        posts = [{'title': r[0], 'subreddit': r[1], 'score': r[2], 'url': r[3]} for r in cur]
        conn.close()
        return posts
    except Exception as e:
        logger.error(f"Error getting post details: {e}")
        return []


def get_trending(limit=30):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow()
    cutoff_24h = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    cutoff_48h = (now - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    cur = conn.execute('''
        SELECT ticker, asset_type, full_name, SUM(count) as total
        FROM mentions WHERE scraped_at >= ?
        GROUP BY ticker ORDER BY total DESC LIMIT ?
    ''', (cutoff_24h, limit))
    current = {row[0]: {'ticker': row[0], 'type': row[1], 'name': row[2], 'mentions': row[3]} for row in cur}

    cur = conn.execute('''
        SELECT ticker, SUM(count) as total FROM mentions
        WHERE scraped_at >= ? AND scraped_at < ?
        GROUP BY ticker
    ''', (cutoff_48h, cutoff_24h))
    previous = {row[0]: row[1] for row in cur}

    # Get prices
    tickers = list(current.keys())
    price_data = {}
    if tickers:
        placeholders = ','.join(['?' for _ in tickers])
        cur = conn.execute(
            f'SELECT ticker, price, change_pct FROM prices WHERE ticker IN ({placeholders})',
            tickers
        )
        price_data = {r[0]: {'price': r[1], 'change': r[2]} for r in cur}

    conn.close()

    results = []
    for ticker, data in current.items():
        prev = previous.get(ticker, 0)
        curr = data['mentions']
        change_pct = round(((curr - prev) / prev) * 100) if prev > 0 else (100 if curr > 0 else 0)
        trend = 'up' if change_pct > 10 else ('down' if change_pct < -10 else 'neutral')

        pd = price_data.get(ticker, {})
        price = pd.get('price')

        results.append({
            'ticker': ticker,
            'name': data['name'],
            'type': data['type'],
            'mentions': curr,
            'prev_mentions': prev,
            'change_pct': change_pct,
            'trend': trend,
            'price': format_price(price),
            'price_change': pd.get('change'),
        })

    results.sort(key=lambda x: x['mentions'], reverse=True)
    return results


def get_last_scraped():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute('SELECT MAX(scraped_at) FROM mentions')
        row = cur.fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception:
        return None

