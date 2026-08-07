# vars.py - Environment variables
import os

API_ID = int(os.environ.get("API_ID", "21705536"))
API_HASH = os.environ.get("API_HASH", "c5bb241f6e3ecf33fe68a444e288de2d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8845555323:AAEUvHekI8V1EXf-L6oCDxHEFD1bcInYGVw")
AUTH_USERS = os.environ.get("AUTH_USERS", "1147534909,5957208798")
WEBHOOK = os.environ.get("WEBHOOK", "false").lower() == "true"
PORT = int(os.environ.get("PORT", 8080))
