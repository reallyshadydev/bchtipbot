from .models import User


def get_address(username):
    """Returns the Dogecoin address (str) of [username]"""
    address = User.get(User.username == username).doge_address
    return address


def count_users():
    """Returns the number of initialised users"""
    return User.select().count()
