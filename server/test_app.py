import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import app


def fixture():
    return {'response': {'status': 'ok', 'currentPage': 1, 'pages': 2, 'total': 11,
                         'results': [{'webTitle': 'Test article', 'webUrl': 'https://www.theguardian.com/world/test',
                                      'webPublicationDate': '2026-01-01T10:00:00Z', 'sectionName': 'World',
                                      'fields': {'trailText': '<p>Text &amp; <strong>details</strong></p>'}}]}}


class GuardianTests(unittest.TestCase):
    def setUp(self):
        app.CACHE.clear()
        app.DAY, app.CALLS, app.LAST_CALL = '', 0, 0
        self.env = patch.dict('os.environ', {'GUARDIAN_API_KEY': 'test-key-not-a-real-secret'})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_parameters(self):
        self.assertEqual(app.parameters('q=climate+change&section=science&page=2'), ('climate change', 'science', 2, '', 'newest'))

    def test_invalid_parameters(self):
        for query in ['q=a&q=b', 'url=https://example.org', 'section=invalid', 'page=0', 'page=51', 'page=x', 'period=year', 'sort=bad', 'q=' + 'a' * 151]:
            with self.subTest(query=query), self.assertRaises(app.ApiError):
                app.parameters(query)

    def test_normalization_and_html(self):
        result = app.normalize(fixture())
        self.assertEqual(result['articles'][0]['description'], 'Text & details')
        self.assertEqual(result['total'], 11)

    def test_unsafe_link_is_rejected(self):
        data = fixture()
        data['response']['results'][0]['webUrl'] = 'https://www.theguardian.com.attacker.example/article'
        self.assertEqual(app.normalize(data)['articles'], [])

    def test_empty_results(self):
        data = fixture()
        data['response'].update(results=[], total=0, pages=0)
        self.assertEqual(app.normalize(data)['articles'], [])

    def test_malformed_provider_response(self):
        for data in [{}, {'response': {'status': 'error'}}, {'response': {'status': 'ok', 'results': []}}]:
            with self.assertRaises(ValueError):
                app.normalize(data)

    def test_missing_key(self):
        with patch.dict('os.environ', {'GUARDIAN_API_KEY': ''}), self.assertRaises(app.ApiError) as error:
            app.get_news()
        self.assertEqual(error.exception.status, 503)

    def test_cache_and_private_key(self):
        with patch('app.urlopen', return_value=io.BytesIO(json.dumps(fixture()).encode())) as network:
            first = app.get_news('climate', 'world', 1)
            self.assertEqual(app.get_news('climate', 'world', 1), first)
            network.assert_called_once()
            self.assertNotIn('test-key', json.dumps(first))
            self.assertIn('q=climate', network.call_args.args[0].full_url)

    def test_provider_rate_limit(self):
        with patch('app.urlopen', side_effect=HTTPError('https://provider.invalid', 429, 'rate limit', {}, None)):
            with self.assertRaises(app.ApiError) as error:
                app.get_news()
        self.assertEqual(error.exception.status, 429)
        self.assertNotIn('test-key', error.exception.message)

    def test_local_rate_limit(self):
        app.LAST_CALL = app.time.monotonic()
        with patch('app.urlopen') as network, self.assertRaises(app.ApiError) as error:
            app.get_news()
        self.assertEqual(error.exception.status, 429)
        network.assert_not_called()

    def test_date_and_sort_forwarded(self):
        with patch('app.urlopen', return_value=io.BytesIO(json.dumps(fixture()).encode())) as network:
            app.get_news('climate', 'science', 1, 'week', 'relevance')
        from urllib.parse import parse_qs, urlsplit
        params = parse_qs(urlsplit(network.call_args.args[0].full_url).query)
        self.assertEqual(params['order-by'], ['relevance'])
        self.assertIn('from-date', params)

    def test_daily_budget(self):
        app.DAY = app.datetime.now(app.timezone.utc).date().isoformat()
        app.CALLS = 450
        with patch('app.urlopen') as network, self.assertRaises(app.ApiError) as error:
            app.get_news()
        self.assertEqual(error.exception.status, 429)
        network.assert_not_called()


class WsgiTests(unittest.TestCase):
    def request(self, path, method='GET', query=''):
        captured = {}
        def start(status, headers):
            captured.update(status=int(status.split()[0]), headers=dict(headers))
        body = app.application({'PATH_INFO': path, 'REQUEST_METHOD': method, 'QUERY_STRING': query}, start)
        try:
            captured['body'] = b''.join(body)
        finally:
            if hasattr(body, 'close'):
                body.close()
        return captured

    def test_health_and_head(self):
        self.assertEqual(self.request('/health')['status'], 200)
        with patch('app.get_news') as news:
            response = self.request('/api/news', 'HEAD')
            self.assertEqual(response['body'], b'')
            news.assert_not_called()

    def test_methods_and_missing_routes(self):
        self.assertEqual(self.request('/api/news', 'POST')['status'], 405)
        self.assertEqual(self.request('/api/unknown')['status'], 404)

    def test_validation_and_safe_provider_error(self):
        self.assertEqual(self.request('/api/news', query='page=0')['status'], 400)
        with patch('app.get_news', side_effect=app.ApiError(429, 'Limit')):
            response = self.request('/api/news')
            self.assertEqual(response['status'], 429)
            self.assertEqual(response['headers']['Retry-After'], '60')
            self.assertEqual(response['headers']['Cache-Control'], 'no-store')
        with patch('app.get_news', side_effect=RuntimeError('private-key')), self.assertLogs('app', level='ERROR') as logs:
            response = self.request('/api/news')
        self.assertEqual(response['status'], 500)
        self.assertNotIn('private-key', str(response) + str(logs.output))

    def test_static_files_and_traversal(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'dist'
            root.mkdir()
            (root / 'index.html').write_text('<h1>Newsroom</h1>')
            (root / '.hidden').write_text('hidden')
            secret = Path(directory) / 'secret'
            secret.write_text('private')
            (root / 'outside').symlink_to(secret)
            with patch('app.DIST', root):
                self.assertEqual(self.request('/')['body'], b'<h1>Newsroom</h1>')
                self.assertEqual(self.request('/', 'HEAD')['body'], b'')
                for path in ['/../secret', '/.hidden', '/outside', '/missing', '/assets/']:
                    self.assertEqual(self.request(path)['status'], 404, path)


if __name__ == '__main__':
    unittest.main()
