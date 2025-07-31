import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Trumpow (TRMP) RPC Configuration
TRMP_RPC_HOST = os.getenv('TRMP_RPC_HOST', 'localhost')
TRMP_RPC_PORT = int(os.getenv('TRMP_RPC_PORT', '22555'))
TRMP_RPC_USER = os.getenv('TRMP_RPC_USER')
TRMP_RPC_PASSWORD = os.getenv('TRMP_RPC_PASSWORD')
TRMP_RPC_WALLET = os.getenv('TRMP_RPC_WALLET', 'tipbot')

if not TRMP_RPC_USER or not TRMP_RPC_PASSWORD:
    raise ValueError("TRMP_RPC_USER and TRMP_RPC_PASSWORD environment variables are required")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trmp_tipbot.db')

# Bot Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))

# Fee Configuration
FEE_ADDRESS = os.getenv('FEE_ADDRESS')
FEE_PERCENTAGE = float(os.getenv('FEE_PERCENTAGE', '0.01'))
MINIMUM_TIP = float(os.getenv('MINIMUM_TIP', '1.0'))
MAXIMUM_TIP = float(os.getenv('MAXIMUM_TIP', '10000.0'))

# Admin Configuration
ADMIN_USERNAMES = os.getenv('ADMIN_USERNAMES', '').split(',')
ADMIN_USERNAMES = [username.strip() for username in ADMIN_USERNAMES if username.strip()]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Legacy compatibility (for any old references)
TOKEN = TELEGRAM_BOT_TOKEN
ADMIN_LIST = ADMIN_USERNAMES
