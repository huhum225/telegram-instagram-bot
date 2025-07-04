web: gunicorn --bind 0.0.0.0:$PORT --worker-class gevent --workers 4 --timeout 120 main:app
worker: python bot.py
