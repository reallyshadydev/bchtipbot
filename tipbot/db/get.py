import logging
from decimal import Decimal
from db.models import User
from trmp_wallet import wallet

logger = logging.getLogger(__name__)


def get_address(username: str) -> str:
    """Get TRMP address for a user"""
    try:
        user = User.select().where(User.username == username).first()
        if user:
            return user.trmp_address
        else:
            logger.warning(f"User {username} not found")
            return ""
    except Exception as e:
        logger.error(f"Failed to get address for {username}: {e}")
        return ""


def get_user_balance(username: str) -> Decimal:
    """Get balance for a user's address"""
    try:
        address = get_address(username)
        if address:
            return wallet.get_balance(address)
        return Decimal('0')
    except Exception as e:
        logger.error(f"Failed to get balance for {username}: {e}")
        return Decimal('0')


def get_user_by_username(username: str) -> User:
    """Get user object by username"""
    try:
        return User.select().where(User.username == username).first()
    except Exception as e:
        logger.error(f"Failed to get user {username}: {e}")
        return None
