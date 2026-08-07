# vars.py - Environment variables
import os

API_ID = int(os.environ.get("API_ID", "21705536"))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK = os.environ.get("WEBHOOK", False)
PORT = int(os.environ.get("PORT", 8080))
