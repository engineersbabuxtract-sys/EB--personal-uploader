# logs.py - Logging configuration
import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory
os.makedirs("/app/logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("/app/logs/bot.log", maxBytes=50000000, backupCount=5),
        logging.StreamHandler(),
    ],
)

# Reduce pyrogram logging
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
