"""Same-origin Guardian API gateway. No API key is sent to the browser."""
import json
import os
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from http import HTTPStatus
import mimetypes
import logging
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
            status = error.code
            error.close()
            if status == 429:
                raise ApiError(429, 'Der Nachrichtenanbieter hat sein Abruflimit erreicht. Bitte später erneut versuchen.') from None
            raise ApiError(502, 'Die Nachrichten-API ist momentan nicht verfügbar.') from None
        except (URLError, TimeoutError, ValueError):
            raise ApiError(502, 'Nachrichten konnten nicht geladen werden. Bitte später erneut versuchen.') from None
        if len(CACHE) >= 64:
            CACHE.popitem(last=False)
        CACHE[key] = (time.monotonic() + 300, result)
        return result


def application(environ, start_response):
    """WSGI entry point used by Gunicorn in production."""
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    headers = [('X-Content-Type-Options', 'nosniff'),
               ('Referrer-Policy', 'strict-origin-when-cross-origin')]

    def respond(status, data, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode()
        response_headers = headers + [('Content-Type', content_type),
                                      ('Content-Length', str(len(body))),
                                      ('Cache-Control', 'no-store')]
        if status == 405:
            response_headers.append(('Allow', 'GET, HEAD'))
        if status == 429:
            response_headers.append(('Retry-After', '60'))
        start_response(f'{status} {HTTPStatus(status).phrase}', response_headers)
        return [] if method == 'HEAD' else [body]

    if method not in ('GET', 'HEAD'):
        return respond(405, {'message': 'Methode nicht erlaubt.'})
    if path == '/health':
        return respond(200, {'status': 'ok'})
    if path == '/api/news':
        # Health checks and HEAD requests must not consume the provider quota.
        if method == 'HEAD':
            return respond(200, {})
        try:
            query = environ.get('QUERY_STRING', '')
            if len(query) > 1000:
                raise ApiError(400, 'Suchanfrage zu lang.')
            return respond(200, get_news(*parameters(query)))
        except ApiError as error:
            return respond(error.status, {'message': error.message})
        except ValueError:
            return respond(400, {'message': 'Ungültige Suchparameter.'})
        except Exception:
            # Never log upstream URLs or exception details containing the key.
            logging.getLogger(__name__).error('Unexpected news gateway failure')
            return respond(500, {'message': 'Interner Serverfehler. Bitte später erneut versuchen.'})
    if path.startswith('/api/'):
        return respond(404, {'message': 'Nicht gefunden.'})

    try:
        root = DIST.resolve()
        file_path = (root / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
        if not file_path.is_relative_to(root) or not file_path.is_file() or any(part.startswith('.') for part in file_path.relative_to(root).parts):
            return respond(404, {'message': 'Nicht gefunden.'})
        file = file_path.open('rb')
    except (OSError, ValueError):
        return respond(404, {'message': 'Nicht gefunden.'})
    size = os.fstat(file.fileno()).st_size
    mime = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
    start_response('200 OK', headers + [('Content-Type', mime),
                                      ('Content-Length', str(size)),
                                      ('Cache-Control', 'no-cache')])
    if method == 'HEAD':
        file.close()
        return []
    wrapper = environ.get('wsgi.file_wrapper')
    if wrapper:
        return wrapper(file, 65536)

    def chunks():
        try:
            while chunk := file.read(65536):
                yield chunk
        finally:
            file.close()
    return chunks()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    # Local development only; Render starts Gunicorn instead.
    with make_server('127.0.0.1', int(os.environ.get('PORT', '8766')), application) as server:
        server.serve_forever()
