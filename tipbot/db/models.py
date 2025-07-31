from peewee import *
import os
import datetime
from urllib.parse import urlparse, uses_netloc
from settings import DEBUG


if DEBUG:
    db = SqliteDatabase("db.sqlite3")
else:
    uses_netloc.append("postgres")
    url = urlparse(os.environ["DATABASE_URL"])
    db = PostgresqlDatabase(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
    )


class User(Model):
    username = CharField(max_length=30, unique=True)
    doge_address = CharField(max_length=54, unique=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
