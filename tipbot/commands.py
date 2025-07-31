import logging
from decimal import Decimal
from telegram import Update
from telegram.ext import CallbackContext

from db.get import get_address, get_user_balance, get_user_by_username
from db.init import create_user
import checks
from settings import FEE_ADDRESS, FEE_PERCENTAGE, MINIMUM_TIP, MAXIMUM_TIP
from rates import get_rate_formatted, convert_trmp_to_currency, is_currency_supported
from trmp_wallet import wallet

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """Start command - creates user if not exists"""
    if not checks.check_username(update):
        return
    
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username
    
    try:
        created = create_user(username)
        if created:
            message = f"Hello {first_name}! Welcome to the TRMP Tip Bot! 🚀\n\n"
            message += "Your TRMP wallet has been created. Type /help to see all available commands."
        else:
            message = f"Hello again, {first_name}! 👋\n\n"
            message += "Type /help to see all available commands."
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        update.message.reply_text("Sorry, there was an error setting up your account. Please try again later.")


def help_command(update: Update, context: CallbackContext) -> None:
    """Show help message with all commands"""
    help_text = """
🤖 *TRMP Tip Bot Commands*

*💰 Wallet Commands:*
/start - Create your TRMP wallet
/deposit - Get your deposit address
/balance - Check your balance
/withdraw <amount> <address> - Withdraw TRMP

*🎯 Tipping Commands:*
/tip <amount> @username - Send TRMP to another user
/tip <amount> satoshi @username - Tip in satoshi

*📊 Price Commands:*
/price - Show current TRMP price (USD)
/price <currency> - Show price in specific currency (eur, btc, eth)

*ℹ️ Info:*
/help - Show this help message

*Example:* `/tip 100 @alice` sends 100 TRMP to @alice
"""
    update.message.reply_text(help_text, parse_mode='Markdown')


def deposit(update: Update, context: CallbackContext) -> None:
    """Show user's deposit address"""
    if not checks.check_username(update):
        return
    
    # Only show address in private messages for security
    if update.message.chat.type != "private":
        update.message.reply_text(
            "🔒 Please send me a private message to see your deposit address for security reasons."
        )
        return
    
    username = update.message.from_user.username
    
    try:
        create_user(username)  # Ensure user exists
        address = get_address(username)
        
        if address:
            message = f"💳 *Your TRMP Deposit Address:*\n\n"
            message += f"`{address}`\n\n"
            message += "Send TRMP to this address to add funds to your tip bot wallet."
            update.message.reply_text(message, parse_mode='Markdown')
        else:
            update.message.reply_text("❌ Error retrieving your deposit address. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in deposit command: {e}")
        update.message.reply_text("❌ Error retrieving your deposit address. Please try again.")


def balance(update: Update, context: CallbackContext) -> None:
    """Show user's balance"""
    if not checks.check_username(update):
        return
    
    username = update.message.from_user.username
    currency = context.args[0].lower() if context.args else "usd"
    
    if not is_currency_supported(currency):
        update.message.reply_text(f"❌ Currency '{currency}' is not supported. Supported currencies: USD, EUR, BTC, ETH")
        return
    
    try:
        create_user(username)  # Ensure user exists
        trmp_balance = get_user_balance(username)
        
        message = f"💰 *Your Balance:*\n\n"
        message += f"**{trmp_balance:.8f} TRMP**\n"
        
        # Show value in requested currency
        if currency != "trmp":
            currency_value = convert_trmp_to_currency(trmp_balance, currency)
            if currency_value:
                if currency == "usd":
                    message += f"≈ ${currency_value:.6f} USD"
                elif currency == "eur":
                    message += f"≈ €{currency_value:.6f} EUR"
                elif currency in ["btc", "eth"]:
                    message += f"≈ {currency_value:.12f} {currency.upper()}"
            else:
                message += f"(Price in {currency.upper()} unavailable)"
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        update.message.reply_text("❌ Error retrieving your balance. Please try again.")


def tip(update: Update, context: CallbackContext) -> None:
    """Send tip to another user"""
    if not checks.check_username(update):
        return
    
    # Check if we have enough arguments
    if len(context.args) < 2:
        update.message.reply_text(
            "❌ Usage: `/tip <amount> @username`\n"
            "Example: `/tip 100 @alice`",
            parse_mode='Markdown'
        )
        return
    
    from_username = update.message.from_user.username
    
    try:
        # Parse amount
        amount_str = context.args[0]
        unit = "trmp"
        
        # Check if amount is in satoshi
        if len(context.args) > 2 and context.args[1].lower() == "satoshi":
            amount = Decimal(amount_str) / Decimal('100000000')  # Convert satoshi to TRMP
            to_username = context.args[2].replace('@', '')
            unit = "satoshi"
        else:
            amount = Decimal(amount_str)
            to_username = context.args[1].replace('@', '')
        
        # Validate amount
        if amount <= 0:
            update.message.reply_text("❌ Amount must be positive.")
            return
        
        if amount < Decimal(str(MINIMUM_TIP)):
            update.message.reply_text(f"❌ Minimum tip amount is {MINIMUM_TIP} TRMP.")
            return
        
        if amount > Decimal(str(MAXIMUM_TIP)):
            update.message.reply_text(f"❌ Maximum tip amount is {MAXIMUM_TIP} TRMP.")
            return
        
        # Check if trying to tip themselves
        if from_username.lower() == to_username.lower():
            update.message.reply_text("❌ You cannot tip yourself!")
            return
        
        # Ensure both users exist
        create_user(from_username)
        to_user = get_user_by_username(to_username)
        if not to_user:
            # Try to create the user (they might not have started the bot yet)
            create_user(to_username)
            to_user = get_user_by_username(to_username)
            if not to_user:
                update.message.reply_text(f"❌ User @{to_username} not found. They need to start the bot first.")
                return
        
        # Check sender's balance
        sender_balance = get_user_balance(from_username)
        
        # Calculate fee (only for tips over 1 TRMP)
        fee = Decimal('0')
        if amount >= Decimal('1') and FEE_PERCENTAGE > 0:
            fee = amount * Decimal(str(FEE_PERCENTAGE))
        
        total_needed = amount + fee
        
        if sender_balance < total_needed:
            update.message.reply_text(
                f"❌ Insufficient balance!\n"
                f"Required: {total_needed:.8f} TRMP (tip: {amount:.8f} + fee: {fee:.8f})\n"
                f"Your balance: {sender_balance:.8f} TRMP"
            )
            return
        
        # Get addresses
        from_address = get_address(from_username)
        to_address = get_address(to_username)
        
        if not from_address or not to_address:
            update.message.reply_text("❌ Error retrieving wallet addresses.")
            return
        
        # Send the tip
        try:
            txid = wallet.send_transaction(to_address, amount, from_address)
            
            # Send fee if applicable
            if fee > 0 and FEE_ADDRESS:
                try:
                    wallet.send_transaction(FEE_ADDRESS, fee, from_address)
                except Exception as e:
                    logger.warning(f"Failed to send fee: {e}")
            
            # Success message
            if unit == "satoshi":
                amount_display = f"{int(amount * 100000000)} satoshi"
            else:
                amount_display = f"{amount:.8f} TRMP"
            
            message = f"✅ *Tip Sent!*\n\n"
            message += f"From: @{from_username}\n"
            message += f"To: @{to_username}\n"
            message += f"Amount: {amount_display}\n"
            if fee > 0:
                message += f"Fee: {fee:.8f} TRMP\n"
            message += f"Transaction: `{txid}`"
            
            update.message.reply_text(message, parse_mode='Markdown')
            
            # Log the transaction
            logger.info(f"Tip sent: {from_username} -> {to_username}, amount: {amount} TRMP, txid: {txid}")
            
        except Exception as e:
            logger.error(f"Failed to send tip: {e}")
            update.message.reply_text("❌ Failed to send tip. Please try again later.")
    
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in tip command: {e}")
        update.message.reply_text("❌ Error processing tip. Please try again.")


def withdraw(update: Update, context: CallbackContext) -> None:
    """Withdraw TRMP to external address"""
    if not checks.check_username(update):
        return
    
    # Only allow withdrawals in private messages for security
    if update.message.chat.type != "private":
        update.message.reply_text(
            "🔒 Please send me a private message to withdraw for security reasons."
        )
        return
    
    if len(context.args) < 2:
        update.message.reply_text(
            "❌ Usage: `/withdraw <amount|all> <address>`\n"
            "Example: `/withdraw 100 TRMPAddressHere`\n"
            "Or: `/withdraw all TRMPAddressHere`",
            parse_mode='Markdown'
        )
        return
    
    username = update.message.from_user.username
    amount_str = context.args[0].lower()
    withdraw_address = context.args[1]
    
    try:
        # Validate withdrawal address
        if not wallet.validate_address(withdraw_address):
            update.message.reply_text("❌ Invalid TRMP address.")
            return
        
        # Check user balance
        create_user(username)
        user_balance = get_user_balance(username)
        
        if user_balance <= 0:
            update.message.reply_text("❌ You have no TRMP to withdraw.")
            return
        
        # Calculate withdrawal amount
        if amount_str == "all":
            # Withdraw all minus a small fee
            withdrawal_fee = Decimal('0.01')  # 0.01 TRMP withdrawal fee
            amount = user_balance - withdrawal_fee
            
            if amount <= 0:
                update.message.reply_text(f"❌ Insufficient balance for withdrawal. Minimum balance needed: {withdrawal_fee} TRMP for fees.")
                return
        else:
            amount = Decimal(amount_str)
            withdrawal_fee = Decimal('0.01')
            
            if amount <= 0:
                update.message.reply_text("❌ Withdrawal amount must be positive.")
                return
            
            if amount + withdrawal_fee > user_balance:
                update.message.reply_text(
                    f"❌ Insufficient balance!\n"
                    f"Requested: {amount:.8f} TRMP\n"
                    f"Fee: {withdrawal_fee:.8f} TRMP\n"
                    f"Total needed: {amount + withdrawal_fee:.8f} TRMP\n"
                    f"Your balance: {user_balance:.8f} TRMP"
                )
                return
        
        # Get user's address
        from_address = get_address(username)
        if not from_address:
            update.message.reply_text("❌ Error retrieving your wallet address.")
            return
        
        # Send withdrawal
        try:
            txid = wallet.send_transaction(withdraw_address, amount, from_address)
            
            message = f"✅ *Withdrawal Successful!*\n\n"
            message += f"Amount: {amount:.8f} TRMP\n"
            message += f"To: `{withdraw_address}`\n"
            message += f"Transaction: `{txid}`\n\n"
            message += "Your TRMP has been sent!"
            
            update.message.reply_text(message, parse_mode='Markdown')
            
            # Log the withdrawal
            logger.info(f"Withdrawal: {username} -> {withdraw_address}, amount: {amount} TRMP, txid: {txid}")
            
        except Exception as e:
            logger.error(f"Failed to process withdrawal: {e}")
            update.message.reply_text("❌ Failed to process withdrawal. Please try again later.")
    
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in withdraw command: {e}")
        update.message.reply_text("❌ Error processing withdrawal. Please try again.")


def price(update: Update, context: CallbackContext) -> None:
    """Show current TRMP price"""
    currency = context.args[0].lower() if context.args else "usd"
    
    if not is_currency_supported(currency):
        supported = ", ".join(["USD", "EUR", "BTC", "ETH"])
        update.message.reply_text(f"❌ Currency '{currency}' not supported. Supported: {supported}")
        return
    
    try:
        price_str = get_rate_formatted(currency)
        
        message = f"💰 *Current TRMP Price*\n\n"
        message += f"**{price_str}**\n\n"
        message += "Price data is updated in real-time from multiple exchanges."
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        update.message.reply_text("❌ Error retrieving price data. Please try again later.")
