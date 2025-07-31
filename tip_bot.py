#!/usr/bin/env python3
"""
Trumpow Telegram Tip Bot

A Telegram bot for sending and receiving Trumpow (TRMP) cryptocurrency.
"""

import asyncio
import logging
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

from config import Config
from trmp_rpc import TrumpowRPC, TrumpowRPCError
from database import DatabaseManager
from wallet_manager import WalletManager


class TrumpowTipBot:
    """Main Trumpow tip bot class."""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.rpc = TrumpowRPC(
            host=self.config.TRMP_RPC_HOST,
            port=self.config.TRMP_RPC_PORT,
            user=self.config.TRMP_RPC_USER,
            password=self.config.TRMP_RPC_PASSWORD,
            wallet=self.config.TRMP_RPC_WALLET
        )
        
        self.db = DatabaseManager(self.config.DATABASE_PATH)
        
        self.wallet_manager = WalletManager(
            rpc_client=self.rpc,
            db_manager=self.db,
            min_tip=self.config.MINIMUM_TIP,
            max_tip=self.config.MAXIMUM_TIP,
            withdrawal_fee=self.config.WITHDRAWAL_FEE,
            confirmation_blocks=self.config.CONFIRMATION_BLOCKS
        )
        
        # Test RPC connection
        if not self.rpc.test_connection():
            raise ConnectionError("Could not connect to Trumpow RPC server")
        
        self.logger.info("Trumpow Tip Bot initialized successfully")
        self.logger.info(self.config.get_summary())
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        try:
            # Create or get user
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            
            welcome_msg = f"""🚀 {self.config.WELCOME_MESSAGE}

🏦 **Your Wallet:**
💰 Balance: {self.wallet_manager.get_user_balance(bot_user)} TRMP
📧 Deposit Address: `{bot_user.trmp_address}`

📱 **Quick Actions:**
• Use /balance to check your balance
• Use /tip <amount> @username to send TRMP
• Use /withdraw <amount> <address> to withdraw
• Use /history to see recent transactions
• Use /help for all commands

🔒 **Security Note:** Always use private messages for sensitive operations like withdrawals."""
            
            await update.message.reply_text(welcome_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ Error creating wallet. Please try again later.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = f"""🤖 **Trumpow Tip Bot Commands**

💰 **Wallet Commands:**
• `/start` - Create your wallet and get started
• `/balance` - Check your TRMP balance
• `/deposit` - Get your deposit address
• `/withdraw <amount> <address>` - Withdraw TRMP (private chat only)
• `/history` - View recent transactions

🎯 **Tipping Commands:**
• `/tip <amount> @username` - Send TRMP to another user
• `/tip <amount> <reply>` - Tip user by replying to their message

📊 **Info Commands:**
• `/help` - Show this help message
• `/stats` - Show bot statistics (admins only)

🔧 **Examples:**
• `/tip 100 @alice` - Send 100 TRMP to alice
• `/withdraw 50 TRMPAddressHere` - Withdraw 50 TRMP
• `/balance` - Check your balance

⚙️ **Settings:**
• Minimum tip: {self.config.MINIMUM_TIP} TRMP
• Maximum tip: {self.config.MAXIMUM_TIP} TRMP
• Withdrawal fee: {self.config.WITHDRAWAL_FEE} TRMP
• Confirmations required: {self.config.CONFIRMATION_BLOCKS}

🔒 **Security:** Use private messages for withdrawals and deposits!"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command."""
        user = update.effective_user
        
        try:
            # Get or create user
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            
            # Get balances
            confirmed_balance = self.wallet_manager.get_user_balance(bot_user)
            unconfirmed_balance = self.wallet_manager.get_user_unconfirmed_balance(bot_user)
            
            balance_msg = f"""💰 **Your TRMP Balance**

✅ **Confirmed:** {confirmed_balance} TRMP
⏳ **Unconfirmed:** {unconfirmed_balance} TRMP
📊 **Total:** {confirmed_balance + unconfirmed_balance} TRMP

📧 **Deposit Address:** `{bot_user.trmp_address}`

Use /deposit to get your deposit address or /tip to send TRMP to others!"""
            
            await update.message.reply_text(balance_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in balance command: {e}")
            await update.message.reply_text("❌ Error getting balance. Please try again later.")
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deposit command."""
        user = update.effective_user
        
        # Check if this is a private chat
        if update.effective_chat.type != 'private':
            await update.message.reply_text("🔒 Please use this command in a private message for security!")
            return
        
        try:
            # Get or create user
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            
            deposit_msg = f"""🏦 **Your Deposit Address**

📧 **Address:** `{bot_user.trmp_address}`

💡 **How to deposit:**
1. Send TRMP to the address above
2. Wait for {self.config.CONFIRMATION_BLOCKS} confirmations
3. Your balance will be updated automatically

⚠️ **Important:** Only send TRMP to this address. Other cryptocurrencies will be lost!"""
            
            await update.message.reply_text(deposit_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in deposit command: {e}")
            await update.message.reply_text("❌ Error getting deposit address. Please try again later.")
    
    async def tip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tip command."""
        user = update.effective_user
        
        # Check rate limits
        try:
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            tips_today, _, _ = self.db.check_rate_limits(user.id)
            
            if tips_today >= self.config.RATE_LIMIT_TIPS_PER_HOUR:
                await update.message.reply_text(f"🚫 Rate limit exceeded. You can send {self.config.RATE_LIMIT_TIPS_PER_HOUR} tips per hour.")
                return
                
        except Exception as e:
            self.logger.error(f"Error checking rate limits: {e}")
            await update.message.reply_text("❌ Error processing tip. Please try again later.")
            return
        
        # Parse command arguments
        if len(context.args) < 2:
            await update.message.reply_text("""❌ **Invalid tip format!**

📝 **Correct usage:**
• `/tip <amount> @username` - Tip a user by username
• Reply to a message and use `/tip <amount>` - Tip by reply

🔧 **Examples:**
• `/tip 100 @alice`
• `/tip 50` (as a reply to someone's message)""", parse_mode='Markdown')
            return
        
        # Parse amount
        amount_str = context.args[0]
        valid, error_msg, amount = self.wallet_manager.validate_amount(amount_str)
        if not valid:
            await update.message.reply_text(f"❌ {error_msg}")
            return
        
        # Find target user
        target_user = None
        
        # Check if replying to a message
        if update.message.reply_to_message:
            target_user_tg = update.message.reply_to_message.from_user
            if target_user_tg.id == user.id:
                await update.message.reply_text("❌ You cannot tip yourself!")
                return
            target_user = self.wallet_manager.create_or_get_user(
                target_user_tg.id, target_user_tg.username or str(target_user_tg.id)
            )
        else:
            # Parse username from command
            target_username = context.args[1].replace('@', '').lower()
            target_user = self.db.get_user_by_username(target_username)
            
            if not target_user:
                await update.message.reply_text(f"❌ User @{target_username} not found. They need to start the bot first!")
                return
        
        # Perform the tip
        try:
            success, message, transaction_id = self.wallet_manager.send_tip(
                bot_user, target_user, amount, 
                f"Tip via Telegram from {user.username or user.id}"
            )
            
            if success:
                # Update rate limits
                self.db.increment_rate_limit(user.id, 'tip')
                
                # Send success message
                success_msg = f"""✅ **Tip Successful!**

💰 Amount: {amount} TRMP
👤 To: @{target_user.username}
💳 Transaction ID: {transaction_id}

🎉 Your tip has been sent successfully!"""
                
                await update.message.reply_text(success_msg, parse_mode='Markdown')
                
                # Notify recipient if it's not a group chat
                if update.effective_chat.type == 'private':
                    try:
                        notify_msg = f"""🎉 **You received a tip!**

💰 Amount: {amount} TRMP
👤 From: @{bot_user.username}
💳 Transaction ID: {transaction_id}

Use /balance to check your updated balance!"""
                        
                        await context.bot.send_message(
                            chat_id=target_user.user_id,
                            text=notify_msg,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not notify recipient: {e}")
            else:
                await update.message.reply_text(f"❌ {message}")
                
        except Exception as e:
            self.logger.error(f"Error in tip command: {e}")
            await update.message.reply_text("❌ Error processing tip. Please try again later.")
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /withdraw command."""
        user = update.effective_user
        
        # Check if this is a private chat
        if update.effective_chat.type != 'private':
            await update.message.reply_text("🔒 Please use this command in a private message for security!")
            return
        
        # Check arguments
        if len(context.args) != 2:
            await update.message.reply_text("""❌ **Invalid withdrawal format!**

📝 **Correct usage:**
`/withdraw <amount> <TRMP_address>`

🔧 **Example:**
`/withdraw 100 TRMPADDRESSHERE`

💡 **Note:** A withdrawal fee of {self.config.WITHDRAWAL_FEE} TRMP will be deducted.""".format(self.config=self.config), parse_mode='Markdown')
            return
        
        try:
            # Get user and check rate limits
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            _, withdrawals_today, withdrawal_amount_today = self.db.check_rate_limits(user.id)
            
            if withdrawals_today >= self.config.RATE_LIMIT_WITHDRAWALS_PER_DAY:
                await update.message.reply_text(f"🚫 Daily withdrawal limit exceeded. You can make {self.config.RATE_LIMIT_WITHDRAWALS_PER_DAY} withdrawals per day.")
                return
            
            # Parse amount
            amount_str = context.args[0]
            valid, error_msg, amount = self.wallet_manager.validate_amount(amount_str)
            if not valid:
                await update.message.reply_text(f"❌ {error_msg}")
                return
            
            # Check daily withdrawal limit
            if withdrawal_amount_today + amount + self.config.WITHDRAWAL_FEE > self.config.MAX_DAILY_WITHDRAWAL:
                remaining = self.config.MAX_DAILY_WITHDRAWAL - withdrawal_amount_today
                await update.message.reply_text(f"🚫 Daily withdrawal limit would be exceeded. You can withdraw {remaining} TRMP more today.")
                return
            
            # Parse address
            address = context.args[1]
            
            # Perform withdrawal
            success, message, transaction_id = self.wallet_manager.withdraw_to_address(
                bot_user, address, amount
            )
            
            if success:
                # Update rate limits
                self.db.increment_rate_limit(user.id, 'withdrawal')
                
                await update.message.reply_text(f"✅ {message}", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ {message}")
                
        except Exception as e:
            self.logger.error(f"Error in withdraw command: {e}")
            await update.message.reply_text("❌ Error processing withdrawal. Please try again later.")
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        user = update.effective_user
        
        try:
            # Get user
            bot_user = self.wallet_manager.create_or_get_user(user.id, user.username or str(user.id))
            
            # Get transaction history
            transactions = self.wallet_manager.get_user_transactions(bot_user, 10)
            
            if not transactions:
                await update.message.reply_text("📭 No transactions found.")
                return
            
            history_msg = "📋 **Recent Transactions**\n\n"
            
            for tx in transactions[:10]:  # Limit to 10 transactions
                history_msg += f"{tx['status_emoji']} {tx['direction']} {tx['description']}\n"
                history_msg += f"💰 {tx['amount']} TRMP • 📅 {tx['date']}\n"
                if tx['txid']:
                    history_msg += f"🔗 `{tx['txid'][:16]}...`\n"
                history_msg += "\n"
            
            await update.message.reply_text(history_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in history command: {e}")
            await update.message.reply_text("❌ Error getting transaction history. Please try again later.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (admin only)."""
        user = update.effective_user
        
        # Check if user is admin
        if not self.config.is_admin(user.username or ""):
            await update.message.reply_text("❌ This command is only available to administrators.")
            return
        
        try:
            # Get bot statistics
            stats = self.db.get_bot_stats()
            network_info = self.wallet_manager.get_network_info()
            wallet_info = self.wallet_manager.get_wallet_info()
            
            stats_msg = f"""📊 **Bot Statistics**

👥 **Users:**
• Total Users: {stats['total_users']}
• Active Users (30d): {stats['active_users']}

💰 **Transactions:**
• Total Transactions: {stats['total_transactions']}
• Total Tips: {stats['total_tips']}
• Tip Volume: {stats['tip_volume']} TRMP

🌐 **Network:**
• Block Height: {network_info.get('block_height', 'Unknown')}
• Connections: {network_info.get('connections', 'Unknown')}
• Network Active: {network_info.get('network_active', 'Unknown')}

🏦 **Wallet:**
• Total Balance: {wallet_info.get('total_balance', 'Unknown')} TRMP
• Account Count: {wallet_info.get('account_count', 'Unknown')}
• Wallet Version: {wallet_info.get('wallet_version', 'Unknown')}"""
            
            await update.message.reply_text(stats_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in stats command: {e}")
            await update.message.reply_text("❌ Error getting statistics. Please try again later.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        self.logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
    
    def run(self):
        """Run the bot."""
        # Create application
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("balance", self.balance_command))
        application.add_handler(CommandHandler("deposit", self.deposit_command))
        application.add_handler(CommandHandler("tip", self.tip_command))
        application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Start the bot
        self.logger.info("Starting Trumpow Tip Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main function."""
    try:
        bot = TrumpowTipBot()
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()