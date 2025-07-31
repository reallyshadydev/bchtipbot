import logging
from decimal import Decimal
from typing import Optional, Tuple, Dict
from datetime import datetime

from trmp_rpc import TrumpowRPC, TrumpowRPCError
from database import DatabaseManager, User, Transaction


class WalletManager:
    """
    Manages user wallets and transactions for the tip bot.
    Integrates with Trumpow RPC client and database.
    """
    
    def __init__(self, rpc_client: TrumpowRPC, db_manager: DatabaseManager, 
                 min_tip: Decimal, max_tip: Decimal, withdrawal_fee: Decimal, 
                 confirmation_blocks: int = 3):
        self.rpc = rpc_client
        self.db = db_manager
        self.min_tip = min_tip
        self.max_tip = max_tip
        self.withdrawal_fee = withdrawal_fee
        self.confirmation_blocks = confirmation_blocks
        self.logger = logging.getLogger(__name__)
    
    def create_or_get_user(self, user_id: int, username: str) -> User:
        """Create a new user or get existing user."""
        # Check if user already exists
        user = self.db.get_user_by_id(user_id)
        if user:
            return user
        
        try:
            # Create new account and address for the user
            account_name = f"user_{user_id}"
            address = self.rpc.create_account_if_not_exists(account_name)
            
            # Create user in database
            user = self.db.create_user(user_id, username, address)
            
            self.logger.info(f"Created new user wallet: {username} -> {address}")
            return user
            
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to create wallet for user {username}: {e}")
            raise
    
    def get_user_balance(self, user: User) -> Decimal:
        """Get user's confirmed balance."""
        try:
            balance = self.rpc.get_balance(user.trmp_account, self.confirmation_blocks)
            return balance
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to get balance for user {user.username}: {e}")
            return Decimal('0')
    
    def get_user_unconfirmed_balance(self, user: User) -> Decimal:
        """Get user's unconfirmed balance."""
        try:
            confirmed = self.rpc.get_balance(user.trmp_account, self.confirmation_blocks)
            total = self.rpc.get_balance(user.trmp_account, 0)
            return total - confirmed
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to get unconfirmed balance for user {user.username}: {e}")
            return Decimal('0')
    
    def send_tip(self, from_user: User, to_user: User, amount: Decimal, 
                 comment: str = "") -> Tuple[bool, str, Optional[int]]:
        """
        Send a tip from one user to another.
        
        Returns:
            (success, message, transaction_id)
        """
        # Validate amount
        if amount < self.min_tip:
            return False, f"Minimum tip amount is {self.min_tip} TRMP", None
        
        if amount > self.max_tip:
            return False, f"Maximum tip amount is {self.max_tip} TRMP", None
        
        # Check sender's balance
        sender_balance = self.get_user_balance(from_user)
        if sender_balance < amount:
            return False, f"Insufficient balance. You have {sender_balance} TRMP", None
        
        try:
            # Create transaction record
            transaction = Transaction(
                id=None,
                from_user_id=from_user.user_id,
                to_user_id=to_user.user_id,
                amount=amount,
                fee=Decimal('0'),
                tx_type='tip',
                status='pending',
                txid=None,
                created_at=datetime.now(),
                comment=comment
            )
            
            transaction_id = self.db.create_transaction(transaction)
            
            # Perform the move operation in Trumpow
            success = self.rpc.move(
                from_user.trmp_account,
                to_user.trmp_account,
                amount,
                self.confirmation_blocks,
                f"Tip from {from_user.username} to {to_user.username}"
            )
            
            if success:
                # Update transaction status
                self.db.update_transaction_status(transaction_id, 'confirmed')
                
                # Update user statistics
                self.db.update_user_tip_stats(from_user.user_id)
                
                self.logger.info(f"Tip successful: {from_user.username} -> {to_user.username} ({amount} TRMP)")
                return True, f"Successfully sent {amount} TRMP to {to_user.username}!", transaction_id
            else:
                self.db.update_transaction_status(transaction_id, 'failed')
                return False, "Transaction failed. Please try again.", transaction_id
                
        except TrumpowRPCError as e:
            self.logger.error(f"Tip failed: {from_user.username} -> {to_user.username}: {e}")
            if transaction_id:
                self.db.update_transaction_status(transaction_id, 'failed')
            return False, f"Transaction failed: {str(e)}", transaction_id
    
    def withdraw_to_address(self, user: User, address: str, amount: Decimal) -> Tuple[bool, str, Optional[int]]:
        """
        Withdraw TRMP to an external address.
        
        Returns:
            (success, message, transaction_id)
        """
        # Validate address
        try:
            addr_info = self.rpc.validate_address(address)
            if not addr_info.get('isvalid', False):
                return False, "Invalid TRMP address", None
        except TrumpowRPCError as e:
            return False, f"Address validation failed: {str(e)}", None
        
        # Calculate total amount needed (including fee)
        total_needed = amount + self.withdrawal_fee
        
        # Check user's balance
        user_balance = self.get_user_balance(user)
        if user_balance < total_needed:
            return False, f"Insufficient balance. You need {total_needed} TRMP (including {self.withdrawal_fee} TRMP fee)", None
        
        try:
            # Create transaction record
            transaction = Transaction(
                id=None,
                from_user_id=user.user_id,
                to_user_id=None,
                amount=amount,
                fee=self.withdrawal_fee,
                tx_type='withdraw',
                status='pending',
                txid=None,
                created_at=datetime.now(),
                to_address=address
            )
            
            transaction_id = self.db.create_transaction(transaction)
            
            # Send the withdrawal
            txid = self.rpc.send_from(
                user.trmp_account,
                address,
                amount,
                self.confirmation_blocks,
                f"Withdrawal for {user.username}",
                f"To: {address}"
            )
            
            # Update transaction with txid
            self.db.update_transaction_status(transaction_id, 'confirmed', txid)
            
            # Update user withdrawal statistics
            self.db.update_user_withdrawal_stats(user.user_id, total_needed)
            
            self.logger.info(f"Withdrawal successful: {user.username} -> {address} ({amount} TRMP, txid: {txid})")
            return True, f"Successfully withdrew {amount} TRMP to {address}!\nTransaction ID: {txid}", transaction_id
            
        except TrumpowRPCError as e:
            self.logger.error(f"Withdrawal failed: {user.username} -> {address}: {e}")
            if transaction_id:
                self.db.update_transaction_status(transaction_id, 'failed')
            return False, f"Withdrawal failed: {str(e)}", transaction_id
    
    def get_deposit_address(self, user: User) -> str:
        """Get user's deposit address."""
        return user.trmp_address
    
    def get_user_transactions(self, user: User, limit: int = 10) -> list:
        """Get formatted transaction history for a user."""
        transactions = self.db.get_user_transactions(user.user_id, limit)
        
        formatted = []
        for tx in transactions:
            # Determine transaction direction and description
            if tx.tx_type == 'tip':
                if tx.from_user_id == user.user_id:
                    # Outgoing tip
                    to_user = self.db.get_user_by_id(tx.to_user_id)
                    direction = "→"
                    description = f"Tip to {to_user.username if to_user else 'Unknown'}"
                    amount_str = f"-{tx.amount}"
                else:
                    # Incoming tip
                    from_user = self.db.get_user_by_id(tx.from_user_id)
                    direction = "←"
                    description = f"Tip from {from_user.username if from_user else 'Unknown'}"
                    amount_str = f"+{tx.amount}"
            
            elif tx.tx_type == 'withdraw':
                direction = "→"
                description = f"Withdrawal to {tx.to_address[:10]}...{tx.to_address[-6:]}"
                amount_str = f"-{tx.amount + tx.fee}"
            
            elif tx.tx_type == 'deposit':
                direction = "←"
                description = f"Deposit from {tx.from_address[:10]}...{tx.from_address[-6:]}" if tx.from_address else "Deposit"
                amount_str = f"+{tx.amount}"
            
            else:
                direction = "?"
                description = tx.tx_type.title()
                amount_str = str(tx.amount)
            
            # Format status
            status_emoji = {
                'confirmed': '✅',
                'pending': '⏳',
                'failed': '❌'
            }.get(tx.status, '❓')
            
            formatted.append({
                'direction': direction,
                'description': description,
                'amount': amount_str,
                'status': tx.status,
                'status_emoji': status_emoji,
                'date': tx.created_at.strftime('%m/%d %H:%M'),
                'txid': tx.txid
            })
        
        return formatted
    
    def check_for_new_deposits(self, user: User) -> list:
        """Check for new deposits for a user."""
        try:
            # Get recent transactions for the user's account
            recent_txs = self.rpc.list_transactions(user.trmp_account, 50, 0)
            
            new_deposits = []
            for tx in recent_txs:
                if (tx['category'] == 'receive' and 
                    tx['confirmations'] >= self.confirmation_blocks and
                    tx['amount'] > 0):
                    
                    # Check if we already have this transaction
                    existing = self.db.get_user_transactions(user.user_id, 100)
                    txid_exists = any(t.txid == tx['txid'] for t in existing if t.txid)
                    
                    if not txid_exists:
                        # Create deposit transaction record
                        deposit = Transaction(
                            id=None,
                            from_user_id=None,
                            to_user_id=user.user_id,
                            amount=Decimal(str(tx['amount'])),
                            fee=Decimal('0'),
                            tx_type='deposit',
                            status='confirmed',
                            txid=tx['txid'],
                            created_at=datetime.fromtimestamp(tx['time']),
                            confirmed_at=datetime.fromtimestamp(tx['time']),
                            to_address=tx.get('address', user.trmp_address)
                        )
                        
                        self.db.create_transaction(deposit)
                        new_deposits.append(deposit)
            
            return new_deposits
            
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to check deposits for user {user.username}: {e}")
            return []
    
    def get_network_info(self) -> Dict:
        """Get network information."""
        try:
            info = self.rpc.get_network_info()
            blockchain_info = self.rpc.get_blockchain_info()
            
            return {
                'connections': info.get('connections', 0),
                'block_height': blockchain_info.get('blocks', 0),
                'difficulty': blockchain_info.get('difficulty', 0),
                'network_active': info.get('networkactive', False)
            }
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to get network info: {e}")
            return {}
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information."""
        try:
            wallet_info = self.rpc.get_wallet_info()
            accounts = self.rpc.list_accounts()
            
            total_balance = sum(accounts.values())
            
            return {
                'total_balance': total_balance,
                'account_count': len(accounts),
                'wallet_version': wallet_info.get('walletversion', 'Unknown'),
                'unlocked_until': wallet_info.get('unlocked_until', 0)
            }
        except TrumpowRPCError as e:
            self.logger.error(f"Failed to get wallet info: {e}")
            return {}
    
    def validate_amount(self, amount_str: str) -> Tuple[bool, str, Optional[Decimal]]:
        """Validate and parse amount string."""
        try:
            amount = Decimal(amount_str)
            
            if amount <= 0:
                return False, "Amount must be positive", None
            
            if amount < self.min_tip:
                return False, f"Minimum amount is {self.min_tip} TRMP", None
            
            if amount > self.max_tip:
                return False, f"Maximum amount is {self.max_tip} TRMP", None
            
            # Check decimal places (max 8 like Bitcoin)
            if amount.as_tuple().exponent < -8:
                return False, "Too many decimal places (max 8)", None
            
            return True, "", amount
            
        except (ValueError, TypeError):
            return False, "Invalid amount format", None