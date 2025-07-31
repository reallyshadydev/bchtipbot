from peewee import IntegrityError
from .models import db, User
from ..dogecoin_client import get_dogecoin_client


def create_user(username):
    """Checks if a Telegram user is present in the database.
    Returns True if a user is created, False otherwise.
    """
    db.connect(reuse_if_open=True)
    client = get_dogecoin_client()
    try:
        # Generate a new Dogecoin address for the user
        doge_address = client.get_new_address(f"user_{username}")
        User.create(username=username, doge_address=doge_address)
        db.close()
        return True
    except IntegrityError:
        db.close()
        return False
