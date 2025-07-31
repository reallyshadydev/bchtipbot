import logging
from db.models import User, db
from trmp_wallet import wallet

logger = logging.getLogger(__name__)


def create_user(username: str) -> bool:
    """
    Create a new user with a TRMP address
    Returns True if user was created, False if user already exists
    """
    try:
        # Check if user already exists
        existing_user = User.select().where(User.username == username).first()
        if existing_user:
            logger.info(f"User {username} already exists")
            return False
        
        # Create new TRMP address for the user
        trmp_address = wallet.get_new_address_for_user(username)
        
        # Create user in database
        User.create(
            username=username,
            trmp_address=trmp_address
        )
        
        logger.info(f"Created new user: {username} with address: {trmp_address}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        return False


def init_database():
    """Initialize database tables"""
    try:
        db.connect()
        db.create_tables([User], safe=True)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
