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


if __name__ == '__main__':
    unittest.main()
