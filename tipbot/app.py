import logging
import os
from telegram.ext import Application, CommandHandler
from commands import start, help_command, deposit, balance, withdraw, tip, price
from admin.commands import stats, wallet_info, backup_users, broadcast, recent_transactions
from settings import TELEGRAM_BOT_TOKEN, DEBUG, WEBHOOK_URL, WEBHOOK_PORT
from db.init import init_database
from db.models import User, Transaction

logger = logging.getLogger(__name__)


def main():
    """Run the TRMP tip bot"""
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Create tables
        from db.models import db
        db.create_tables([User, Transaction], safe=True)
        logger.info("Database tables created/verified")
        
        # Create application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        logger.info("Setting up command handlers...")
        
        # Basic commands
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Wallet commands
        application.add_handler(CommandHandler("deposit", deposit))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("withdraw", withdraw))
        
        # Tipping commands
        application.add_handler(CommandHandler("tip", tip))
        
        # Price commands
        application.add_handler(CommandHandler("price", price))
        
        # Admin commands
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CommandHandler("wallet_info", wallet_info))
        application.add_handler(CommandHandler("backup_users", backup_users))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CommandHandler("recent_transactions", recent_transactions))
        
        logger.info("Command handlers set up successfully")
        
        # Start the bot
        if DEBUG:
            logger.info("Starting bot in polling mode (DEBUG=True)")
            application.run_polling(allowed_updates=["message"])
        else:
            if not WEBHOOK_URL:
                logger.error("WEBHOOK_URL must be set for production mode")
                return
            
            logger.info(f"Starting bot in webhook mode at {WEBHOOK_URL}")
            
            # Get the app name from environment or default
            app_name = os.environ.get("HEROKU_APP_NAME", "trmp-tipbot")
            
            # Start webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=WEBHOOK_PORT,
                url_path=TELEGRAM_BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}",
                allowed_updates=["message"]
            )
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
