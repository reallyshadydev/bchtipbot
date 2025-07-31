import logging
import re
from telegram import Update
from trmp_wallet import wallet

logger = logging.getLogger(__name__)


def check_username(update: Update) -> bool:
    """
    Check if user has a valid Telegram username
    
    Args:
        update: Telegram update object
        
    Returns:
        True if username is valid, False otherwise
    """
    if not update.message.from_user.username:
        update.message.reply_text(
            "❌ You need to set a Telegram username to use this bot.\n\n"
            "To set a username:\n"
            "1. Go to Telegram Settings\n"
            "2. Edit Profile\n"
            "3. Add a username\n"
            "4. Try again"
        )
        return False
    return True


def check_address(address: str) -> bool:
    """
    Validate TRMP address format
    
    Args:
        address: TRMP address string
        
    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False
    
    try:
        return wallet.validate_address(address)
    except Exception as e:
        logger.error(f"Error validating address {address}: {e}")
        return False


def check_amount(amount_str: str) -> tuple:
    """
    Validate and parse amount string
    
    Args:
        amount_str: Amount as string
        
    Returns:
        Tuple of (is_valid: bool, amount: float or None, error_message: str or None)
    """
    if not amount_str:
        return False, None, "Amount cannot be empty"
    
    # Remove common currency symbols
    cleaned_amount = amount_str.replace('$', '').replace(',', '').strip()
    
    try:
        amount = float(cleaned_amount)
        
        if amount <= 0:
            return False, None, "Amount must be positive"
        
        if amount > 1000000:  # 1 million TRMP max
            return False, None, "Amount too large"
        
        # Check for reasonable decimal places (max 8 for TRMP)
        if '.' in cleaned_amount:
            decimal_places = len(cleaned_amount.split('.')[1])
            if decimal_places > 8:
                return False, None, "Too many decimal places (max 8)"
        
        return True, amount, None
        
    except ValueError:
        return False, None, "Invalid number format"


def username_is_valid(username: str) -> bool:
    """
    Check if username format is valid
    
    Args:
        username: Username string
        
    Returns:
        True if valid format, False otherwise
    """
    if not username:
        return False
    
    # Remove @ if present
    username = username.replace('@', '')
    
    # Telegram username requirements:
    # - 5-32 characters
    # - Can contain a-z, 0-9, and underscores
    # - Must start with a letter
    # - Cannot end with underscore
    # - Cannot have consecutive underscores
    
    if len(username) < 5 or len(username) > 32:
        return False
    
    if not re.match(r'^[a-zA-Z]', username):
        return False
    
    if username.endswith('_'):
        return False
    
    if '__' in username:
        return False
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    
    return True


def amount_is_valid(amount_str: str) -> bool:
    """
    Simple amount validation (backward compatibility)
    
    Args:
        amount_str: Amount as string
        
    Returns:
        True if valid, False otherwise
    """
    is_valid, _, _ = check_amount(amount_str)
    return is_valid


def validate_tip_amount(amount: float, min_tip: float = 1.0, max_tip: float = 10000.0) -> tuple:
    """
    Validate tip amount against limits
    
    Args:
        amount: Tip amount
        min_tip: Minimum allowed tip
        max_tip: Maximum allowed tip
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if amount < min_tip:
        return False, f"Minimum tip amount is {min_tip} TRMP"
    
    if amount > max_tip:
        return False, f"Maximum tip amount is {max_tip} TRMP"
    
    return True, None


def check_rate_limit(user_id: int, command: str) -> bool:
    """
    Check if user is rate limited for a command
    Note: This is a placeholder for future rate limiting implementation
    
    Args:
        user_id: Telegram user ID
        command: Command name
        
    Returns:
        True if allowed, False if rate limited
    """
    # TODO: Implement rate limiting using Redis or in-memory cache
    # For now, always allow
    return True


def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        input_str: User input string
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove potential harmful characters
    sanitized = re.sub(r'[<>"\';\\]', '', input_str)
    
    # Limit length
    return sanitized[:100]


def is_private_chat(update: Update) -> bool:
    """
    Check if message is from a private chat
    
    Args:
        update: Telegram update object
        
    Returns:
        True if private chat, False otherwise
    """
    return update.message.chat.type == "private"


def is_group_chat(update: Update) -> bool:
    """
    Check if message is from a group chat
    
    Args:
        update: Telegram update object
        
    Returns:
        True if group chat, False otherwise
    """
    return update.message.chat.type in ["group", "supergroup"]


def format_trmp_amount(amount: float, decimals: int = 8) -> str:
    """
    Format TRMP amount for display
    
    Args:
        amount: TRMP amount
        decimals: Number of decimal places
        
    Returns:
        Formatted amount string
    """
    return f"{amount:.{decimals}f}".rstrip('0').rstrip('.')


def validate_withdraw_amount(amount: float, balance: float, min_withdraw: float = 0.01) -> tuple:
    """
    Validate withdrawal amount
    
    Args:
        amount: Withdrawal amount
        balance: User balance
        min_withdraw: Minimum withdrawal amount
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if amount < min_withdraw:
        return False, f"Minimum withdrawal amount is {min_withdraw} TRMP"
    
    # Add fee for calculation
    withdrawal_fee = 0.01
    total_needed = amount + withdrawal_fee
    
    if total_needed > balance:
        return False, f"Insufficient balance. Need {total_needed} TRMP (including {withdrawal_fee} TRMP fee), have {balance} TRMP"
    
    return True, None
