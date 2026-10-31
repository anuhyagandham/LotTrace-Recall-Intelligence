"""
Root application entry point for LotTrace AI.
Exposes Flask WSGI application for local development or production servers.
"""

from api import app, create_app
from config import API_HOST, API_PORT
from src.utils.logging_config import logger

if __name__ == "__main__":
    logger.info(f"Launching LotTrace AI Application on http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=True)
