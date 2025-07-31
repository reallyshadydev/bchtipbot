import os
import logging
from decimal import Decimal
from typing import List
from dotenv import load_dotenv


class Config:
    """Configuration manager for the Trumpow tip bot."""
    
    def __init__(self, env_file: str = '.env'):
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        # Trumpow RPC Configuration
        self.TRMP_RPC_HOST = os.getenv('TRMP_RPC_HOST', 'localhost')
        self.TRMP_RPC_PORT = int(os.getenv('TRMP_RPC_PORT', '22555'))
        self.TRMP_RPC_USER = os.getenv('TRMP_RPC_USER')
        self.TRMP_RPC_PASSWORD = os.getenv('TRMP_RPC_PASSWORD')
        self.TRMP_RPC_WALLET = os.getenv('TRMP_RPC_WALLET', 'tipbot')
        
        if not self.TRMP_RPC_USER or not self.TRMP_RPC_PASSWORD:
            raise ValueError("TRMP_RPC_USER and TRMP_RPC_PASSWORD are required")
        
        # Bot Settings
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        self.MINIMUM_TIP = Decimal(os.getenv('MINIMUM_TIP', '1.0'))
        self.MAXIMUM_TIP = Decimal(os.getenv('MAXIMUM_TIP', '10000.0'))
        self.WITHDRAWAL_FEE = Decimal(os.getenv('WITHDRAWAL_FEE', '0.1'))
        self.CONFIRMATION_BLOCKS = int(os.getenv('CONFIRMATION_BLOCKS', '3'))
        
        # Database Configuration
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', './tip_bot.db')
        
        # Security Settings
        self.RATE_LIMIT_TIPS_PER_HOUR = int(os.getenv('RATE_LIMIT_TIPS_PER_HOUR', '10'))
        self.RATE_LIMIT_WITHDRAWALS_PER_DAY = int(os.getenv('RATE_LIMIT_WITHDRAWALS_PER_DAY', '5'))
        self.MAX_DAILY_WITHDRAWAL = Decimal(os.getenv('MAX_DAILY_WITHDRAWAL', '1000.0'))
        
        # Admin Configuration
        admin_usernames = os.getenv('ADMIN_USERNAMES', '')
        self.ADMIN_USERNAMES = [username.strip() for username in admin_usernames.split(',') if username.strip()]
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE = os.getenv('LOG_FILE', './tip_bot.log')
        
        # Custom Messages
        self.WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE', 
                                       'Welcome to the Trumpow Tip Bot! Use /help to get started.')
        self.HELP_MESSAGE = os.getenv('HELP_MESSAGE',
                                    'Use /balance to check your balance, /tip to send TRMP to others, /deposit to get your address.')
        
        # Setup logging
        self._setup_logging()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.LOG_LEVEL, logging.INFO)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler
        try:
            file_handler = logging.FileHandler(self.LOG_FILE)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            logging.warning(f"Could not create log file {self.LOG_FILE}: {e}")
    
    def _validate_config(self):
        """Validate configuration values."""
        errors = []
        
        # Validate amounts
        if self.MINIMUM_TIP <= 0:
            errors.append("MINIMUM_TIP must be positive")
        
        if self.MAXIMUM_TIP <= 0:
            errors.append("MAXIMUM_TIP must be positive")
        
        if self.MINIMUM_TIP >= self.MAXIMUM_TIP:
            errors.append("MINIMUM_TIP must be less than MAXIMUM_TIP")
        
        if self.WITHDRAWAL_FEE < 0:
            errors.append("WITHDRAWAL_FEE cannot be negative")
        
        if self.CONFIRMATION_BLOCKS < 0:
            errors.append("CONFIRMATION_BLOCKS cannot be negative")
        
        # Validate rate limits
        if self.RATE_LIMIT_TIPS_PER_HOUR < 0:
            errors.append("RATE_LIMIT_TIPS_PER_HOUR cannot be negative")
        
        if self.RATE_LIMIT_WITHDRAWALS_PER_DAY < 0:
            errors.append("RATE_LIMIT_WITHDRAWALS_PER_DAY cannot be negative")
        
        if self.MAX_DAILY_WITHDRAWAL < 0:
            errors.append("MAX_DAILY_WITHDRAWAL cannot be negative")
        
        # Validate RPC port
        if not (1 <= self.TRMP_RPC_PORT <= 65535):
            errors.append("TRMP_RPC_PORT must be between 1 and 65535")
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)
        
        logging.info("Configuration validated successfully")
    
    def is_admin(self, username: str) -> bool:
        """Check if a username is an admin."""
        return username.lower() in [admin.lower() for admin in self.ADMIN_USERNAMES]
    
    def get_summary(self) -> str:
        """Get a summary of the configuration (without sensitive data)."""
        return f"""Trumpow Tip Bot Configuration:
- RPC Host: {self.TRMP_RPC_HOST}:{self.TRMP_RPC_PORT}
- RPC Wallet: {self.TRMP_RPC_WALLET}
- Minimum Tip: {self.MINIMUM_TIP} TRMP
- Maximum Tip: {self.MAXIMUM_TIP} TRMP
- Withdrawal Fee: {self.WITHDRAWAL_FEE} TRMP
- Confirmation Blocks: {self.CONFIRMATION_BLOCKS}
- Rate Limits: {self.RATE_LIMIT_TIPS_PER_HOUR} tips/hour, {self.RATE_LIMIT_WITHDRAWALS_PER_DAY} withdrawals/day
- Max Daily Withdrawal: {self.MAX_DAILY_WITHDRAWAL} TRMP
- Admins: {len(self.ADMIN_USERNAMES)} configured
- Debug Mode: {self.DEBUG}
- Log Level: {self.LOG_LEVEL}
- Database: {self.DATABASE_PATH}"""