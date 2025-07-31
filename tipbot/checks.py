# Functions checking for incorrect inputs
from dogecoin_client import get_dogecoin_client
import logging

logger = logging.getLogger(__name__)


def check_username(update):
    """
    Checks for username.
    Returns True if user has a uname set up, False otherwise
    """
    if not update.message.from_user.username:
        update.message.reply_text(
            "You do not have a username. Please create "
            "one in settings to use this bot."
        )
        return False
    return True


def amount_is_valid(amount):
    """Checks if [amount] is a valid Dogecoin amount"""
    try:
        amount = float(amount)
        if amount <= 0:
            return False
        # Check if amount is reasonable (not too many decimal places)
        if len(str(amount).split('.')[-1]) > 8:
            return False
    except Exception:
        return False

    return True


def username_is_valid(username):
    """Checks if a Telegram username is valid"""
    if username[0] != "@":
        return False
    username = username[1:]  # remove the '@'
    if len(username) < 5 or len(username) > 30:
        return False
    # TODO: check for special characters
    return True


def check_address(update, address):
    """
    Checks if a Dogecoin address is correct using Dogecoin Core RPC

    Returns the address if correct, False otherwise
    """
    try:
        client = get_dogecoin_client()
        if client.validate_address(address):
            return address
        else:
            message = f"{address} is not a valid Dogecoin address."
            update.message.reply_text(message)
            return False
    except Exception as e:
        logger.error(f"Error validating address {address}: {e}")
        message = f"Unable to validate address {address}. Please check and try again."
        update.message.reply_text(message)
        return False
