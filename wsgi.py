"""Gunicorn entrypoint. Heroku runs `gunicorn wsgi:app`."""
from app import app  # noqa

if __name__ == "__main__":
    app.run()
