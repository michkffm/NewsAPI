import unittest
from unittest.mock import patch
import app
from app import parse_feed

class FeedTests(unittest.TestCase):
    def test_only_valid_br_links(self):
        raw = b'<rss><channel><item><title>News</title><link>https://www.br.de/news</link><description>Text</description></item><item><title>Bad</title><link>javascript:alert(1)</link></item></channel></rss>'
        articles = parse_feed(raw)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['description'], 'Text')

    def test_empty_and_broken_feed(self):
        for raw in [b'<rss/>', b'broken']:
            with self.assertRaises(ValueError if raw == b'<rss/>' else Exception):
                parse_feed(raw)

    def test_network_failure_does_not_serve_expired_news(self):
        app.CACHE = [{'title': 'old'}]
        app.EXPIRES = 0
        with patch('app.urlopen', side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                app.get_news()
        self.assertIsNone(app.CACHE)

    def test_fresh_cache_avoids_network(self):
        app.CACHE = [{'title': 'cached'}]
        app.EXPIRES = float('inf')
        with patch('app.urlopen') as request:
            self.assertEqual(app.get_news(), app.CACHE)
            request.assert_not_called()
        app.CACHE = None
        app.EXPIRES = 0

if __name__ == '__main__':
    unittest.main()
