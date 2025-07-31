from peewee import *
import os
from urllib.parse import urlparse, uses_netloc
from settings import DEBUG, DATABASE_URL


if DEBUG:
    # For development, use SQLite
    if DATABASE_URL.startswith('sqlite:'):
        db_path = DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
        db = SqliteDatabase(db_path)
    else:
        db = SqliteDatabase("trmp_tipbot.db")
else:
    # For production, parse DATABASE_URL
    uses_netloc.append("postgres")
    uses_netloc.append("postgresql")
    url = urlparse(DATABASE_URL)
    
    if url.scheme in ['postgres', 'postgresql']:
        db = PostgresqlDatabase(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )
    else:
        # Fallback to SQLite
        db_path = DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
        db = SqliteDatabase(db_path)


class User(Model):
    """User model for tip bot users"""
    username = CharField(max_length=50, unique=True)
    trmp_address = CharField(max_length=100, unique=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    is_active = BooleanField(default=True)
    
    class Meta:
        database = db


class Transaction(Model):
    """Transaction model for tracking tips and withdrawals"""
    from_user = ForeignKeyField(User, backref='sent_transactions', null=True)
    to_user = ForeignKeyField(User, backref='received_transactions', null=True)
    amount = DecimalField(max_digits=20, decimal_places=8)
    fee = DecimalField(max_digits=20, decimal_places=8, default=0)
    txid = CharField(max_length=100, null=True)
    tx_type = CharField(max_length=20)  # 'tip', 'withdraw', 'deposit'
    status = CharField(max_length=20, default='pending')  # 'pending', 'confirmed', 'failed'
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    external_address = CharField(max_length=100, null=True)  # For withdrawals
    
    class Meta:
        database = db
