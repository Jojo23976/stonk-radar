import requests
import re
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from collections import Counter

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

# Tickers that are too ambiguous without the $ prefix
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
    'EOW', 'EOY', 'IRL', 'AMA', 'AFAIK', 'IMO', 'IMHO', 'FYI',
    'LMAO', 'LMFAO', 'ROFL', 'SMH', 'TIL', 'IIRC', 'DAE', 'CMV',
    'ELI', 'EDIT', 'UPDATE', 'EDIT2', 'EDIT3', 'OP',
}

DB_PATH = 'sentiment.db'


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
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ticker_time ON mentions(ticker, scraped_at)')
    conn.commit()
    conn.close()


def extract_mentions(text):
    mentions = Counter()
    if not text:
        return mentions

    # $TICKER pattern (explicit, highest confidence)
    dollar_matches = re.findall(r'\$([A-Za-z]{1,6})\b', text)
    for match in dollar_matches:
        ticker = match.upper()
        if ticker in STOCK_TICKERS:
            mentions[('stock', ticker)] += 3
        elif ticker in CRYPTO_ASSETS:
            mentions[('crypto', ticker)] += 3

    # Plain uppercase tickers (only from known lists, filtered)
    words = re.findall(r'\b([A-Z]{2,6})\b', text)
    for word in words:
        if word in IGNORE_WORDS:
            continue
        if word in AMBIGUOUS_TICKERS:
            continue
        if word in STOCK_TICKERS:
            mentions[('stock', word)] += 1
        elif word in CRYPTO_ASSETS:
            mentions[('crypto', word)] += 1

    # Full crypto names
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
                        'num_comments': d.get('num_comments', 0),
                    })
            time.sleep(1.5)
        except Exception as e:
            logger.warning(f"Error fetching r/{subreddit}/{sort}: {e}")
    return posts


def scrape_all():
    logger.info("Starting Reddit scrape...")
    all_mentions = Counter()

    for subreddit in SUBREDDITS:
        posts = fetch_subreddit(subreddit)
        logger.info(f"r/{subreddit}: {len(posts)} posts fetched")
        for post in posts:
            text = post['title'] + ' ' + post['selftext']
            mentions = extract_mentions(text)
            # Weight by post score (popular posts count more)
            weight = max(1, min(5, 1 + post['score'] // 1000))
            for key, count in mentions.items():
                all_mentions[key] += count * weight

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    for (asset_type, ticker), count in all_mentions.items():
        if asset_type == 'stock':
            full_name = STOCK_TICKERS.get(ticker, ticker)
        else:
            full_name = CRYPTO_ASSETS.get(ticker, ticker)
        conn.execute(
            'INSERT INTO mentions (ticker, asset_type, full_name, count, scraped_at) VALUES (?,?,?,?,?)',
            (ticker, asset_type, full_name, count, now)
        )
    conn.commit()
    conn.close()
    logger.info(f"Scrape done. {len(all_mentions)} assets tracked.")


def get_trending(limit=30):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow()
    cutoff_24h = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    cutoff_48h = (now - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

    # Last 24h
    cur = conn.execute('''
        SELECT ticker, asset_type, full_name, SUM(count) as total
        FROM mentions
        WHERE scraped_at >= ?
        GROUP BY ticker
        ORDER BY total DESC
        LIMIT ?
    ''', (cutoff_24h, limit))
    current = {row[0]: {'ticker': row[0], 'type': row[1], 'name': row[2], 'mentions': row[3]} for row in cur}

    # Previous 24h (24-48h ago)
    cur = conn.execute('''
        SELECT ticker, SUM(count) as total
        FROM mentions
        WHERE scraped_at >= ? AND scraped_at < ?
        GROUP BY ticker
    ''', (cutoff_48h, cutoff_24h))
    previous = {row[0]: row[1] for row in cur}

    conn.close()

    results = []
    for ticker, data in current.items():
        prev = previous.get(ticker, 0)
        curr = data['mentions']
        if prev > 0:
            change_pct = round(((curr - prev) / prev) * 100)
        elif curr > 0:
            change_pct = 100
        else:
            change_pct = 0

        if change_pct > 10:
            trend = 'up'
        elif change_pct < -10:
            trend = 'down'
        else:
            trend = 'neutral'

        results.append({
            'ticker': ticker,
            'name': data['name'],
            'type': data['type'],
            'mentions': curr,
            'prev_mentions': prev,
            'change_pct': change_pct,
            'trend': trend,
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
