import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "")
    XROCKET_TOKEN = os.getenv("XROCKET_TOKEN", "")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    HOUSE_EDGE = float(os.getenv("HOUSE_EDGE", "0.05"))

config = Config()