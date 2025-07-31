import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define settings
try:
    DEBUG = os.getenv("DEBUG", "True") == "True"  # because DEBUG is a string
except KeyError:
    DEBUG = True

try:
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")
except KeyError:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")

# Your output Dogecoin address for fees
FEE_ADDRESS = os.getenv("FEE_ADDRESS")
if not FEE_ADDRESS:
    raise ValueError("FEE_ADDRESS must be set in .env file")

# The fee you want to charge (0.01 is 1%)
try:
    FEE_PERCENTAGE = float(os.getenv("FEE_PERCENTAGE", "0.01"))
except ValueError:
    FEE_PERCENTAGE = 0.01

# List of administrators allowed to use the admin commands
ADMIN_LIST_STR = os.getenv("ADMIN_LIST", "")
ADMIN_LIST = [admin.strip() for admin in ADMIN_LIST_STR.split(",") if admin.strip()]
