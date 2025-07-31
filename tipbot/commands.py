from time import sleep
from decimal import Decimal
import logging

from telegram import Update
from telegram.ext import CallbackContext

from db.get import get_address
from db.init import create_user
from dogecoin_client import get_dogecoin_client
import checks
from settings import FEE_ADDRESS, FEE_PERCENTAGE
from rates import get_rate, format_price, convert_doge_to_currency, convert_currency_to_doge, is_currency_supported

logger = logging.getLogger(__name__)


def start(update: Update, _: CallbackContext):
    """Starts the bot.
    Create a database entry for [username] unless it exists already.
    """
    if not checks.check_username(update):
        return
    first_name = update.message.from_user.first_name
    info = ". Type /help for the list of commands."

    created = create_user(update.message.from_user.username)
    if created:
        return update.message.reply_text("Hello " + first_name + info)
    else:
        return update.message.reply_text("Hello again, " + first_name + info)


def deposit(update: Update, _: CallbackContext):
    """
    Fetches and returns the Dogecoin address saved in the db if the command
    was sent in a direct message. Asks to send DM otherwise.
    """
    if not checks.check_username(update):
        return
    if update.message.chat.type != "private":  # check if in DM
        return update.message.reply_html(
            text="Private message me to see your deposit address",
        )

    create_user(update.message.from_user.username)  # check if user is created
    address = get_address(update.message.from_user.username)
    update.message.reply_text("Send Dogecoin to:")
    return update.message.reply_html(f"<b>{address}</b>")


def balance(update, context: CallbackContext):
    """Fetches and returns the balance"""
    currency = context.args[0].lower() if context.args else "usd"
    
    if not checks.check_username(update):
        return
    if update.message.chat.type != "private":  # check if in DM
        return update.message.reply_html(
            text="Private message me to see your balance",
        )

    create_user(update.message.from_user.username)
    address = get_address(update.message.from_user.username)
    
    try:
        client = get_dogecoin_client()
        doge_balance = client.get_balance(address)
        
        if currency == "doge" or currency == "dogecoin":
            message = f"You have: {doge_balance:.8f} DOGE"
        else:
            if not is_currency_supported(currency):
                return update.message.reply_text(f"{currency} is not a supported currency")
            
            converted_balance = convert_doge_to_currency(doge_balance, currency)
            if converted_balance is None:
                return update.message.reply_text("Unable to fetch current exchange rate")
            
            formatted_balance = format_price(converted_balance, currency)
            message = f"You have: {formatted_balance} ({doge_balance:.8f} DOGE)"
        
        return update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return update.message.reply_text("Unable to fetch balance. Please try again later.")


def withdraw(update, context: CallbackContext):
    """Withdraws DOGE to user's wallet"""
    if not checks.check_username(update):
        return

    if update.message.chat.type != "private":  # check if in DM
        return update.message.reply_html(
            text="Private message me to withdraw your money",
        )

    if len(context.args) != 2:
        message = (
            "Usage: /withdraw [amount] [address]\n\n"
            "You may also withdraw everything at once using:"
            " /withdraw all [address]"
        )
        return update.message.reply_text(message)

    address = checks.check_address(update, context.args[1])
    if not address:  # does not send anything if address is False
        return

    username = update.message.from_user.username
    user_address = get_address(username)
    
    try:
        client = get_dogecoin_client()
        current_balance = client.get_balance(user_address)
        
        if current_balance <= 0:
            return update.message.reply_text("You don't have any funds to withdraw!")
        
        if context.args[0] == "all":
            # Withdraw all funds minus a small fee for the transaction
            amount = current_balance - Decimal('0.01')  # Leave 0.01 DOGE for tx fee
            if amount <= 0:
                return update.message.reply_text("Insufficient balance to cover transaction fee!")
        else:
            amount_str = context.args[0].replace("$", "")
            if not checks.amount_is_valid(amount_str):
                return update.message.reply_text(f"{amount_str} is not a valid amount")
            
            amount = Decimal(amount_str)
            if amount > current_balance:
                return update.message.reply_text("You don't have enough funds!")
        
        # Send the transaction
        tx_id = client.send_to_address(address, amount, f"Withdrawal for {username}")
        
        return update.message.reply_text(f"Sent! Transaction ID: {tx_id}")
        
    except Exception as e:
        logger.error(f"Withdrawal error: {e}")
        return update.message.reply_text(f"Transaction failed: {str(e)}")


def help_command(update: Update, _: CallbackContext):
    """Displays the help text"""
    return update.message.reply_text(
        """/start - Starts the bot
/deposit - Displays your Dogecoin address for top up
/balance - Shows your balance in Dogecoin
/withdraw - Withdraw your funds. Usage: /withdraw [amount] [address]
/help - Lists all commands
/tip - Sends a tip. Usage: /tip [amount] [@username]
/price - Displays the current price of Dogecoin"""
    )


def tip(update, context: CallbackContext):
    """Sends Dogecoin tip"""
    if not checks.check_username(update):
        return

    args = context.args

    if len(args) < 2 and not update.message.reply_to_message:
        return update.message.reply_text("Usage: /tip [amount] [username]")

    if "@" in args[0]:
        # this swaps args[0] and args[1] in case user input username before
        # amount (e.g. /tip @username 10) - the latter will still work
        tmp = args[1]
        args[1] = args[0]
        args[0] = tmp

    amount_str = args[0].replace("$", "")
    if not checks.amount_is_valid(amount_str):
        return update.message.reply_text(f"{amount_str} is not a valid amount.")

    amount = Decimal(amount_str)

    if update.message.reply_to_message:
        recipient_username = update.message.reply_to_message.from_user.username
        if not recipient_username:
            return update.message.reply_text(
                "You cannot tip someone who has not set a username."
            )
    else:
        recipient_username = args[1]
        if not checks.username_is_valid(recipient_username):
            return update.message.reply_text(
                f"{recipient_username} is not a valid username."
            )

    recipient_username = recipient_username.replace("@", "")
    sender_username = update.message.from_user.username

    if recipient_username == sender_username:
        return update.message.reply_text("You cannot send money to yourself.")

    # Create recipient user if they don't exist
    create_user(recipient_username)
    recipient_address = get_address(recipient_username)
    sender_address = get_address(sender_username)

    try:
        client = get_dogecoin_client()
        sender_balance = client.get_balance(sender_address)
        
        # Check if sender has enough balance
        if amount > sender_balance:
            return update.message.reply_text(
                "You don't have enough funds! Type /deposit to add funds!"
            )

        # Calculate fee (only for tips over 1 DOGE)
        fee = Decimal('0')
        if amount >= Decimal('1'):
            fee = amount * Decimal(str(FEE_PERCENTAGE))
            if fee < Decimal('0.01'):  # Minimum fee
                fee = Decimal('0')

        total_amount = amount + fee
        if total_amount > sender_balance:
            return update.message.reply_text(
                "You don't have enough funds to cover the tip and fee!"
            )

        # Create transaction outputs
        outputs = []
        
        # Send tip to recipient
        tx_id_tip = client.send_to_address(recipient_address, amount, f"Tip from {sender_username}")
        
        # Send fee if applicable
        if fee > 0:
            tx_id_fee = client.send_to_address(FEE_ADDRESS, fee, f"Fee from tip by {sender_username}")
        
        message = f"You sent {amount:.8f} DOGE to @{recipient_username}"
        if fee > 0:
            message += f" (fee: {fee:.8f} DOGE)"
            
        return update.message.reply_html(text=message)
        
    except Exception as e:
        logger.error(f"Tip error: {e}")
        return update.message.reply_text(f"Transaction failed: {str(e)}")


def price(update, context: CallbackContext):
    """Fetches and returns the price of DOGE"""
    currency = context.args[0].lower() if context.args else "usd"
    
    if not is_currency_supported(currency):
        supported = ", ".join(["usd", "eur", "gbp", "btc", "eth"])
        return update.message.reply_text(
            f"{currency} is not supported. Supported currencies: {supported}"
        )

    doge_price = get_rate(currency)
    if doge_price is None:
        return update.message.reply_text("Unable to fetch current price. Please try again later.")
    
    formatted_price = format_price(doge_price, currency)
    return update.message.reply_text(f"1 DOGE = {formatted_price}")
