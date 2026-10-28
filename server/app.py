"""Small same-origin RSS gateway; Python standard library only."""
import json
import os
import time
import threading
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

FEED = 'https://nachrichtenfeeds.br.de/rss/nachrichten/seiten/QXAPkQJ'
DIST = Path(__file__).resolve().parents[1] / 'dist'
LOCK = threading.Lock()
CACHE = None
EXPIRES = 0


def parse_feed(raw):
    root = ET.fromstring(raw)
    articles = []
    for item in root.findall('./channel/item')[:60]:
        title = item.findtext('title', '').strip()
        url = item.findtext('link', '').strip()
        parsed = urlsplit(url)
        if not title or parsed.scheme != 'https' or parsed.hostname != 'www.br.de':
            continue
        articles.append({'title': title, 'url': url,
                         'description': item.findtext('description', ''),
                         'publishedAt': item.findtext('pubDate', ''),
                         'category': item.findtext('category', '')})
    if not articles:
        raise ValueError('Empty feed')
    return articles


def get_news():
    global CACHE, EXPIRES
    with LOCK:
        if CACHE is not None and time.monotonic() < EXPIRES:
            return CACHE
        # Discard expired contents: no persistent storage or news archive.
        CACHE = None
        request = Request(FEED, headers={'User-Agent': 'NewsApp-RSS/1.0'})
        with urlopen(request, timeout=12) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Feed too large')
        CACHE = parse_feed(raw)
        EXPIRES = time.monotonic() + 300
        return CACHE


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/news':
            try:
                self.send_json(200, {'articles': get_news()})
            except Exception:
                self.send_json(502, {'message': 'Nachrichten sind gerade nicht erreichbar. Bitte später erneut versuchen.'})
        elif path.startswith('/api/'):
            self.send_json(404, {'message': 'Nicht gefunden.'})
        else:
            super().do_GET()

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def list_directory(self, path):
        self.send_error(404)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8766'))), Handler).serve_forever()
