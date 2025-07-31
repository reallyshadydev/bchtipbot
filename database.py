import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class User:
    """User data class."""
    user_id: int
    username: str
    trmp_account: str
    trmp_address: str
    created_at: datetime
    is_active: bool = True
    last_tip_time: Optional[datetime] = None
    daily_tip_count: int = 0
    daily_withdrawal_amount: Decimal = Decimal('0')
    last_reset_date: Optional[datetime] = None


@dataclass
class Transaction:
    """Transaction data class."""
    id: Optional[int]
    from_user_id: Optional[int]
    to_user_id: Optional[int]
    amount: Decimal
    fee: Decimal
    tx_type: str  # 'tip', 'withdraw', 'deposit'
    status: str   # 'pending', 'confirmed', 'failed'
    txid: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    comment: Optional[str] = None


class DatabaseManager:
    """Database manager for the tip bot."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    trmp_account TEXT UNIQUE NOT NULL,
                    trmp_address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    last_tip_time TIMESTAMP,
                    daily_tip_count INTEGER DEFAULT 0,
                    daily_withdrawal_amount DECIMAL DEFAULT 0,
                    last_reset_date DATE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    amount DECIMAL NOT NULL,
                    fee DECIMAL DEFAULT 0,
                    tx_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    txid TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    from_address TEXT,
                    to_address TEXT,
                    comment TEXT,
                    FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                    FOREIGN KEY (to_user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    tips_today INTEGER DEFAULT 0,
                    withdrawals_today INTEGER DEFAULT 0,
                    last_reset_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (from_user_id, to_user_id)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_txid ON transactions (txid)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at)''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def create_user(self, user_id: int, username: str, trmp_address: str) -> User:
        """Create a new user."""
        # Generate a unique account name for the user
        account_hash = hashlib.sha256(f"{user_id}_{username}_{secrets.token_hex(8)}".encode()).hexdigest()[:16]
        trmp_account = f"user_{account_hash}"
        
        user = User(
            user_id=user_id,
            username=username,
            trmp_account=trmp_account,
            trmp_address=trmp_address,
            created_at=datetime.now()
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO users (user_id, username, trmp_account, trmp_address, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.user_id, user.username, user.trmp_account, user.trmp_address, user.created_at))
            
            # Initialize rate limits
            conn.execute('''
                INSERT INTO rate_limits (user_id, last_reset_date)
                VALUES (?, ?)
            ''', (user.user_id, datetime.now().date()))
            
            conn.commit()
        
        self.logger.info(f"Created new user: {username} (ID: {user_id})")
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    trmp_account=row['trmp_account'],
                    trmp_address=row['trmp_address'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active']),
                    last_tip_time=datetime.fromisoformat(row['last_tip_time']) if row['last_tip_time'] else None,
                    daily_tip_count=row['daily_tip_count'],
                    daily_withdrawal_amount=Decimal(str(row['daily_withdrawal_amount'])),
                    last_reset_date=datetime.fromisoformat(row['last_reset_date']).date() if row['last_reset_date'] else None
                )
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM users WHERE username = ? COLLATE NOCASE
            ''', (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    trmp_account=row['trmp_account'],
                    trmp_address=row['trmp_address'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active']),
                    last_tip_time=datetime.fromisoformat(row['last_tip_time']) if row['last_tip_time'] else None,
                    daily_tip_count=row['daily_tip_count'],
                    daily_withdrawal_amount=Decimal(str(row['daily_withdrawal_amount'])),
                    last_reset_date=datetime.fromisoformat(row['last_reset_date']).date() if row['last_reset_date'] else None
                )
            return None
    
    def update_user_tip_stats(self, user_id: int):
        """Update user's tip statistics."""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            # Reset daily counters if it's a new day
            conn.execute('''
                UPDATE users 
                SET daily_tip_count = CASE 
                    WHEN last_reset_date != ? THEN 1
                    ELSE daily_tip_count + 1
                END,
                last_tip_time = ?,
                last_reset_date = ?
                WHERE user_id = ?
            ''', (today, datetime.now(), today, user_id))
            
            conn.commit()
    
    def update_user_withdrawal_stats(self, user_id: int, amount: Decimal):
        """Update user's withdrawal statistics."""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            # Reset daily counters if it's a new day
            conn.execute('''
                UPDATE users 
                SET daily_withdrawal_amount = CASE 
                    WHEN last_reset_date != ? THEN ?
                    ELSE daily_withdrawal_amount + ?
                END,
                last_reset_date = ?
                WHERE user_id = ?
            ''', (today, amount, amount, today, user_id))
            
            conn.commit()
    
    def create_transaction(self, transaction: Transaction) -> int:
        """Create a new transaction record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO transactions 
                (from_user_id, to_user_id, amount, fee, tx_type, status, txid, 
                 created_at, from_address, to_address, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.from_user_id,
                transaction.to_user_id,
                str(transaction.amount),
                str(transaction.fee),
                transaction.tx_type,
                transaction.status,
                transaction.txid,
                transaction.created_at,
                transaction.from_address,
                transaction.to_address,
                transaction.comment
            ))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            
        self.logger.info(f"Created transaction {transaction_id}: {transaction.tx_type}")
        return transaction_id
    
    def update_transaction_status(self, transaction_id: int, status: str, txid: str = None):
        """Update transaction status."""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'confirmed':
                conn.execute('''
                    UPDATE transactions 
                    SET status = ?, confirmed_at = ?, txid = COALESCE(?, txid)
                    WHERE id = ?
                ''', (status, datetime.now(), txid, transaction_id))
            else:
                conn.execute('''
                    UPDATE transactions 
                    SET status = ?, txid = COALESCE(?, txid)
                    WHERE id = ?
                ''', (status, txid, transaction_id))
            
            conn.commit()
    
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Get recent transactions for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM transactions 
                WHERE from_user_id = ? OR to_user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, user_id, limit))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(
                    id=row['id'],
                    from_user_id=row['from_user_id'],
                    to_user_id=row['to_user_id'],
                    amount=Decimal(str(row['amount'])),
                    fee=Decimal(str(row['fee'])),
                    tx_type=row['tx_type'],
                    status=row['status'],
                    txid=row['txid'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    confirmed_at=datetime.fromisoformat(row['confirmed_at']) if row['confirmed_at'] else None,
                    from_address=row['from_address'],
                    to_address=row['to_address'],
                    comment=row['comment']
                ))
            
            return transactions
    
    def get_pending_transactions(self) -> List[Transaction]:
        """Get all pending transactions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM transactions 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            ''')
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(
                    id=row['id'],
                    from_user_id=row['from_user_id'],
                    to_user_id=row['to_user_id'],
                    amount=Decimal(str(row['amount'])),
                    fee=Decimal(str(row['fee'])),
                    tx_type=row['tx_type'],
                    status=row['status'],
                    txid=row['txid'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    confirmed_at=datetime.fromisoformat(row['confirmed_at']) if row['confirmed_at'] else None,
                    from_address=row['from_address'],
                    to_address=row['to_address'],
                    comment=row['comment']
                ))
            
            return transactions
    
    def check_rate_limits(self, user_id: int) -> Tuple[int, int, Decimal]:
        """Check user's current rate limits. Returns (tips_today, withdrawals_today, withdrawal_amount_today)."""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT tips_today, withdrawals_today, last_reset_date FROM rate_limits WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                # Create rate limit entry for new user
                conn.execute('''
                    INSERT INTO rate_limits (user_id, last_reset_date) VALUES (?, ?)
                ''', (user_id, today))
                conn.commit()
                return 0, 0, Decimal('0')
            
            # Check if we need to reset daily counters
            last_reset = datetime.fromisoformat(row['last_reset_date']).date() if row['last_reset_date'] else today
            if last_reset != today:
                conn.execute('''
                    UPDATE rate_limits 
                    SET tips_today = 0, withdrawals_today = 0, last_reset_date = ?
                    WHERE user_id = ?
                ''', (today, user_id))
                conn.commit()
                return 0, 0, Decimal('0')
            
            # Get user's daily withdrawal amount
            user_cursor = conn.execute('''
                SELECT daily_withdrawal_amount, last_reset_date FROM users WHERE user_id = ?
            ''', (user_id,))
            user_row = user_cursor.fetchone()
            
            withdrawal_amount = Decimal('0')
            if user_row:
                user_last_reset = datetime.fromisoformat(user_row['last_reset_date']).date() if user_row['last_reset_date'] else today
                if user_last_reset == today:
                    withdrawal_amount = Decimal(str(user_row['daily_withdrawal_amount']))
            
            return row['tips_today'], row['withdrawals_today'], withdrawal_amount
    
    def increment_rate_limit(self, user_id: int, limit_type: str):
        """Increment a rate limit counter."""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            if limit_type == 'tip':
                conn.execute('''
                    UPDATE rate_limits 
                    SET tips_today = tips_today + 1, last_reset_date = ?
                    WHERE user_id = ?
                ''', (today, user_id))
            elif limit_type == 'withdrawal':
                conn.execute('''
                    UPDATE rate_limits 
                    SET withdrawals_today = withdrawals_today + 1, last_reset_date = ?
                    WHERE user_id = ?
                ''', (today, user_id))
            
            conn.commit()
    
    def get_bot_stats(self) -> Dict:
        """Get bot statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total users
            total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
            
            # Active users (used bot in last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            active_users = conn.execute('''
                SELECT COUNT(*) as count FROM users 
                WHERE last_tip_time > ? OR created_at > ?
            ''', (thirty_days_ago, thirty_days_ago)).fetchone()['count']
            
            # Total transactions
            total_transactions = conn.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
            
            # Total tips
            total_tips = conn.execute('''
                SELECT COUNT(*) as count FROM transactions WHERE tx_type = 'tip'
            ''').fetchone()['count']
            
            # Total tip volume
            tip_volume = conn.execute('''
                SELECT COALESCE(SUM(amount), 0) as volume FROM transactions 
                WHERE tx_type = 'tip' AND status = 'confirmed'
            ''').fetchone()['volume']
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_transactions': total_transactions,
                'total_tips': total_tips,
                'tip_volume': Decimal(str(tip_volume))
            }