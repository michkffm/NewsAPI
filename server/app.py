"""Same-origin Guardian API gateway. No API key is sent to the browser."""
import json
import os
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

DIST = Path(__file__).resolve().parents[1] / 'dist'
SECTIONS = {'', 'world', 'technology', 'science', 'business', 'sport', 'environment'}
LOCK = threading.Lock()
CACHE = OrderedDict()
LAST_CALL = 0.0
DAY = ''
CALLS = 0


class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)


def text_only(value):
    parser = PlainText()
    parser.feed(value if isinstance(value, str) else '')
    return ''.join(parser.parts)


def parameters(query):
    params = parse_qs(query, keep_blank_values=True, max_num_fields=5)
    if set(params) - {'q', 'section', 'page', 'period', 'sort'} or any(len(v) != 1 for v in params.values()):
        raise ApiError(400, 'Ungültige Suchparameter.')
    q = params.get('q', [''])[0].strip()
    section = params.get('section', [''])[0]
    page = params.get('page', ['1'])[0]
    period = params.get('period', [''])[0]
    sort = params.get('sort', ['newest'])[0]
    if period not in ('', 'day', 'week', 'month') or sort not in ('newest', 'relevance'):
        raise ApiError(400, 'Ungültiger Zeitraum oder Sortierung.')
    if len(q) > 150 or any(ord(c) < 32 for c in q) or section not in SECTIONS or not page.isascii() or not page.isdigit() or not 1 <= int(page) <= 50:
        raise ApiError(400, 'Bitte Suchbegriff, Thema und Seite prüfen.')
    return q, section, int(page), period, sort


def normalize(data):
    response = data.get('response') if isinstance(data, dict) else None
    if not isinstance(response, dict) or response.get('status') != 'ok' or not isinstance(response.get('results'), list):
        raise ValueError('Invalid provider response')
    articles = []
    for item in response['results']:
        if not isinstance(item, dict):
            raise ValueError('Invalid article')
        url, title = item.get('webUrl'), item.get('webTitle')
        if not isinstance(url, str) or not isinstance(title, str):
            raise ValueError('Invalid article fields')
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname != 'www.theguardian.com' or parsed.username or parsed.password:
            continue
        published = item.get('webPublicationDate', '')
        category = item.get('sectionName', '')
        if not isinstance(published, str) or not isinstance(category, str):
            raise ValueError('Invalid article metadata')
        fields = item.get('fields', {})
        articles.append({'title': title, 'url': url,
                         'description': text_only(fields.get('trailText', '') if isinstance(fields, dict) else ''),
                         'publishedAt': published,
                         'category': category})
    counts = [response.get(k) for k in ('currentPage', 'pages', 'total')]
    if any(type(n) is not int or n < 0 for n in counts):
        raise ValueError('Invalid pagination')
    return dict(articles=articles, page=counts[0], pages=counts[1], total=counts[2])


def get_news(q='', section='', page=1, period='', sort='newest'):
    global DAY, CALLS, LAST_CALL
    api_key = os.environ.get('GUARDIAN_API_KEY', '').strip()
    if not api_key:
        raise ApiError(503, 'Die Nachrichten-API ist noch nicht eingerichtet.')
    key = (q, section, page, period, sort, datetime.now(timezone.utc).date().isoformat())
    with LOCK:
        now = time.monotonic()
        for expired in [k for k, (expires, _) in CACHE.items() if expires <= now]:
            del CACHE[expired]
        if key in CACHE:
            return CACHE[key][1]
        today = datetime.now(timezone.utc).date().isoformat()
        if DAY != today:
            DAY, CALLS = today, 0
        if CALLS >= 450:
            raise ApiError(429, 'Das Tageskontingent ist erreicht. Bitte morgen erneut versuchen.')
        if now - LAST_CALL < 1.1:
            raise ApiError(429, 'Bitte kurz warten und erneut versuchen.')
        params = {'api-key': api_key, 'page-size': 10, 'page': page,
                  'order-by': sort, 'show-fields': 'trailText'}
        if period:
            days = {'day': 1, 'week': 7, 'month': 30}[period]
            params['from-date'] = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec='seconds').replace('+00:00', 'Z')
        if q:
            params['q'] = q
        if section:
            params['section'] = section
        CALLS += 1
        LAST_CALL = now
        request = Request('https://content.guardianapis.com/search?' + urlencode(params),
                          headers={'User-Agent': 'MichaelKoch-NewsApp/1.0'})
        try:
            with urlopen(request, timeout=12) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError('Response too large')
            result = normalize(json.loads(raw))
        except HTTPError as error:
            if error.code == 429:
                raise ApiError(429, 'Der Nachrichtenanbieter hat sein Abruflimit erreicht. Bitte später erneut versuchen.') from None
            raise ApiError(502, 'Die Nachrichten-API ist momentan nicht verfügbar.') from None
        except (URLError, TimeoutError, ValueError):
            raise ApiError(502, 'Nachrichten konnten nicht geladen werden. Bitte später erneut versuchen.') from None
        if len(CACHE) >= 64:
            CACHE.popitem(last=False)
        CACHE[key] = (time.monotonic() + 300, result)
        return result


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == '/api/news':
            try:
                if len(request.query) > 1000:
                    raise ApiError(400, 'Suchanfrage zu lang.')
                result = get_news(*parameters(request.query))
                self.send_json(200, result)
            except ApiError as error:
                self.send_json(error.status, {'message': error.message})
            except ValueError:
                self.send_json(400, {'message': 'Ungültige Suchparameter.'})
        elif request.path == '/health':
            self.send_json(200, {'status': 'ok'})
        elif request.path.startswith('/api/'):
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
        if status == 429:
            self.send_header('Retry-After', '60')
        self.end_headers()
        self.wfile.write(body)

    def list_directory(self, path):
        self.send_error(404)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8766'))), Handler).serve_forever()
