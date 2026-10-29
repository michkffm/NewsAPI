"""One process shares the cache and provider budget across bounded threads."""
import os

bind = '0.0.0.0:' + os.environ.get('PORT', '8766')
workers = 1
worker_class = 'gthread'
threads = 4
timeout = 30
graceful_timeout = 20
keepalive = 2
limit_request_line = 2048
limit_request_fields = 50
limit_request_field_size = 4096
# Provider URLs contain the API key; never enable verbose request/debug logging.
accesslog = None
loglevel = 'warning'
