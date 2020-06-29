web: gunicorn wsgi:app --workers=1 --threads=2 --timeout=60 --bind 0.0.0.0:$PORT
worker: python -m src.stream
