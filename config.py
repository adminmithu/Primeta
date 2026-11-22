import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
