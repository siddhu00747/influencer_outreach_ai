import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
GOOGLE_OAUTH_CLIENT_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SENDER_NAME = os.getenv("SENDER_NAME", "Your Name")
SENDER_COMPANY = os.getenv("SENDER_COMPANY", "Your Brand")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
FOLLOWUP1_DAYS = int(os.getenv("FOLLOWUP1_DAYS", "4"))
FOLLOWUP2_DAYS = int(os.getenv("FOLLOWUP2_DAYS", "6"))
