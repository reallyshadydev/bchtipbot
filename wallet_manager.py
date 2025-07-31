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
                 comment: str = "", use_raw_transactions: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Send a tip from one user to another.
        
        Args:
            from_user: Sender user
            to_user: Recipient user
            amount: Amount to tip
            comment: Optional comment
            use_raw_transactions: Whether to use raw transactions (avoids change) vs account moves
        
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
            
            if use_raw_transactions:
                # Use raw transaction approach for tips (creates on-chain transaction)
                try:
                    from_addresses = self.rpc.get_addresses_by_account(from_user.trmp_account)
                    to_address = to_user.trmp_address
                    
                    max_fee = Decimal('0.01')  # Max fee for tips
                    success, result, raw_tx = self.build_raw_transaction_no_change(
                        from_addresses, to_address, amount, max_fee
                    )
                    
                    if success:
                        txid = result
                        self.db.update_transaction_status(transaction_id, 'confirmed', txid)
                        self.db.update_user_tip_stats(from_user.user_id)
                        
                        self.logger.info(f"Raw tip successful: {from_user.username} -> {to_user.username} ({amount} TRMP, txid: {txid})")
                        return True, f"Successfully sent {amount} TRMP to {to_user.username}! (On-chain transaction)", transaction_id
                    else:
                        # Fall back to account move if raw transaction fails
                        self.logger.warning(f"Raw tip failed, falling back to account move: {result}")
                        use_raw_transactions = False
                        
                except Exception as e:
                    self.logger.warning(f"Raw tip failed, falling back to account move: {e}")
                    use_raw_transactions = False
            
            if not use_raw_transactions:
                # Use account move operation (off-chain, internal to wallet)
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
            if 'transaction_id' in locals():
                self.db.update_transaction_status(transaction_id, 'failed')
            return False, f"Transaction failed: {str(e)}", transaction_id if 'transaction_id' in locals() else None
    
    def withdraw_to_address(self, user: User, address: str, amount: Decimal) -> Tuple[bool, str, Optional[int]]:
        """
        Withdraw TRMP to an external address using raw transactions to avoid change addresses.
        
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
        
        # Check user's balance first
        user_balance = self.get_user_balance(user)
        if user_balance < amount:
            return False, f"Insufficient balance. You have {user_balance} TRMP", None
        
        # Get user's addresses to spend from
        try:
            user_addresses = self.rpc.get_addresses_by_account(user.trmp_account)
            if not user_addresses:
                return False, "No addresses found for user account", None
        except TrumpowRPCError as e:
            return False, f"Failed to get user addresses: {str(e)}", None
        
        try:
            # Create transaction record
            transaction = Transaction(
                id=None,
                from_user_id=user.user_id,
                to_user_id=None,
                amount=amount,
                fee=Decimal('0'),  # Fee will be calculated by raw transaction builder
                tx_type='withdraw',
                status='pending',
                txid=None,
                created_at=datetime.now(),
                to_address=address
            )
            
            transaction_id = self.db.create_transaction(transaction)
            
            # Build raw transaction without change address
            max_fee = min(self.withdrawal_fee, amount * Decimal('0.1'))  # Cap fee at 10% of amount
            success, result, raw_tx = self.build_raw_transaction_no_change(
                user_addresses, address, amount, max_fee
            )
            
            if not success:
                self.db.update_transaction_status(transaction_id, 'failed')
                return False, f"Failed to create transaction: {result}", transaction_id
            
            # result contains the txid if successful
            txid = result
            
            # Calculate actual fee used
            try:
                # Get transaction details to find actual fee
                tx_info = self.rpc.get_transaction(txid)
                actual_fee = abs(Decimal(str(tx_info.get('fee', 0))))
            except:
                actual_fee = max_fee  # Fallback to estimated fee
            
            # Update transaction with txid and actual fee
            self.db.update_transaction_status(transaction_id, 'confirmed', txid)
            # Update the fee in the transaction record
            # Note: You may need to add a method to update transaction fee in database.py
            
            # Update user withdrawal statistics  
            total_cost = amount + actual_fee
            self.db.update_user_withdrawal_stats(user.user_id, total_cost)
            
            self.logger.info(f"Withdrawal successful (no-change): {user.username} -> {address} ({amount} TRMP, fee: {actual_fee}, txid: {txid})")
            return True, f"Successfully withdrew {amount} TRMP to {address}!\nTransaction ID: {txid}\nNetwork fee: {actual_fee} TRMP", transaction_id
            
        except Exception as e:
            self.logger.error(f"Withdrawal failed: {user.username} -> {address}: {e}")
            if 'transaction_id' in locals():
                self.db.update_transaction_status(transaction_id, 'failed')
            return False, f"Withdrawal failed: {str(e)}", transaction_id if 'transaction_id' in locals() else None
    
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
    
    def build_raw_transaction_no_change(self, from_addresses: list, to_address: str, 
                                       amount: Decimal, max_fee: Decimal = Decimal('0.01')) -> Tuple[bool, str, Optional[str]]:
        """
        Build a raw transaction without change addresses by selecting UTXOs that minimize leftover.
        
        Args:
            from_addresses: List of addresses to spend from
            to_address: Destination address
            amount: Amount to send
            max_fee: Maximum acceptable fee
            
        Returns:
            (success, message_or_txid, raw_transaction_hex)
        """
        try:
            # Get all unspent outputs for the addresses
            all_utxos = []
            for addr in from_addresses:
                utxos = self.rpc.list_unspent(self.confirmation_blocks, 9999999, [addr])
                for utxo in utxos:
                    utxo['address'] = addr
                    all_utxos.append(utxo)
            
            if not all_utxos:
                return False, "No unspent outputs available", None
            
            # Sort UTXOs by amount (ascending) to prefer smaller UTXOs first
            all_utxos.sort(key=lambda x: Decimal(str(x['amount'])))
            
            # Find the best combination of UTXOs that minimizes leftover (avoids change)
            best_combination = self._find_best_utxo_combination(all_utxos, amount, max_fee)
            
            if not best_combination:
                return False, f"Cannot create transaction without change. Available UTXOs don't match required amount closely enough.", None
            
            # Build the transaction inputs
            inputs = []
            for utxo in best_combination['utxos']:
                inputs.append({
                    "txid": utxo['txid'],
                    "vout": utxo['vout']
                })
            
            # Build the transaction outputs - only destination, no change
            total_input = best_combination['total_input']
            actual_fee = total_input - amount
            
            if actual_fee > max_fee:
                return False, f"Required fee ({actual_fee}) exceeds maximum ({max_fee})", None
            
            outputs = {to_address: float(amount)}
            
            # Create raw transaction
            raw_tx = self.rpc.create_raw_transaction(inputs, outputs)
            
            # Sign the transaction
            signed_result = self.rpc.sign_raw_transaction(raw_tx)
            
            if not signed_result.get('complete', False):
                return False, "Failed to sign transaction completely", None
            
            # Send the transaction
            txid = self.rpc.send_raw_transaction(signed_result['hex'])
            
            self.logger.info(f"Created no-change transaction: {txid}, fee: {actual_fee}")
            return True, txid, signed_result['hex']
            
        except Exception as e:
            self.logger.error(f"Failed to build raw transaction: {e}")
            return False, str(e), None
    
    def _find_best_utxo_combination(self, utxos: list, target_amount: Decimal, 
                                   max_fee: Decimal) -> Optional[Dict]:
        """
        Find the best combination of UTXOs that gets as close as possible to target_amount + reasonable_fee
        without going under, to avoid creating change outputs.
        
        This uses a greedy approach optimized for minimizing leftover amount.
        """
        target_amount = Decimal(str(target_amount))
        max_fee = Decimal(str(max_fee))
        min_fee = Decimal('0.0001')  # Minimum network fee
        
        # Try different strategies to find UTXOs without change
        
        # Strategy 1: Find a single UTXO that matches closely
        for utxo in utxos:
            utxo_amount = Decimal(str(utxo['amount']))
            leftover = utxo_amount - target_amount
            
            # Perfect match or small leftover that can be used as fee
            if min_fee <= leftover <= max_fee:
                return {
                    'utxos': [utxo],
                    'total_input': utxo_amount,
                    'leftover': leftover
                }
        
        # Strategy 2: Find minimal combination that works
        # Sort by amount descending for this strategy
        utxos_desc = sorted(utxos, key=lambda x: Decimal(str(x['amount'])), reverse=True)
        
        for i in range(len(utxos_desc)):
            for j in range(i + 1, min(i + 5, len(utxos_desc))):  # Limit combinations to avoid long computation
                combo_utxos = utxos_desc[i:j+1]
                total = sum(Decimal(str(u['amount'])) for u in combo_utxos)
                leftover = total - target_amount
                
                if min_fee <= leftover <= max_fee:
                    return {
                        'utxos': combo_utxos,
                        'total_input': total,
                        'leftover': leftover
                    }
        
        # Strategy 3: Exact amount combinations (rare but perfect)
        # Try combinations that sum to exactly target_amount + small_fee
        for fee in [Decimal('0.0001'), Decimal('0.001'), Decimal('0.01')]:
            if fee > max_fee:
                continue
                
            exact_target = target_amount + fee
            
            # Use subset sum approach for small sets
            if len(utxos) <= 20:
                combination = self._find_exact_sum_combination(utxos, exact_target)
                if combination:
                    return {
                        'utxos': combination,
                        'total_input': exact_target,
                        'leftover': fee
                    }
        
        return None
    
    def _find_exact_sum_combination(self, utxos: list, target: Decimal) -> Optional[list]:
        """Find a combination of UTXOs that sum to exactly the target amount."""
        target = Decimal(str(target))
        
        # Dynamic programming approach for subset sum
        n = len(utxos)
        if n > 15:  # Limit to avoid exponential explosion
            return None
        
        # Convert to integers for DP (multiply by 100000000 to handle 8 decimal places)
        multiplier = 100000000
        target_int = int(target * multiplier)
        amounts = [int(Decimal(str(utxo['amount'])) * multiplier) for utxo in utxos]
        
        # Check all combinations (2^n)
        for mask in range(1, 1 << n):
            total = 0
            combination = []
            
            for i in range(n):
                if mask & (1 << i):
                    total += amounts[i]
                    combination.append(utxos[i])
            
            if total == target_int:
                return combination
        
        return None
    
    def get_utxo_summary(self, user: User) -> Dict:
        """Get a summary of user's UTXOs for analysis."""
        try:
            addresses = self.rpc.get_addresses_by_account(user.trmp_account)
            all_utxos = []
            
            for addr in addresses:
                utxos = self.rpc.list_unspent(self.confirmation_blocks, 9999999, [addr])
                for utxo in utxos:
                    utxo['address'] = addr
                    all_utxos.append(utxo)
            
            if not all_utxos:
                return {
                    'total_utxos': 0,
                    'total_amount': Decimal('0'),
                    'largest_utxo': Decimal('0'),
                    'smallest_utxo': Decimal('0'),
                    'average_utxo': Decimal('0'),
                    'no_change_possible': []
                }
            
            amounts = [Decimal(str(utxo['amount'])) for utxo in all_utxos]
            total_amount = sum(amounts)
            
            # Find amounts that could be sent without change (within reasonable fee range)
            no_change_amounts = []
            max_fee = Decimal('0.01')
            min_fee = Decimal('0.0001')
            
            for utxo_amount in amounts:
                # Single UTXO transactions
                if min_fee <= utxo_amount <= total_amount:
                    max_sendable = utxo_amount - min_fee
                    min_sendable = utxo_amount - max_fee
                    if min_sendable > 0:
                        no_change_amounts.append((min_sendable, max_sendable))
            
            return {
                'total_utxos': len(all_utxos),
                'total_amount': total_amount,
                'largest_utxo': max(amounts),
                'smallest_utxo': min(amounts),
                'average_utxo': total_amount / len(amounts),
                'no_change_possible': no_change_amounts[:10]  # Top 10 possibilities
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get UTXO summary for {user.username}: {e}")
            return {}
    
    def estimate_transaction_fee(self, from_addresses: list, amount: Decimal) -> Tuple[Decimal, bool]:
        """
        Estimate the fee required for a transaction and whether it can be done without change.
        
        Returns:
            (estimated_fee, can_avoid_change)
        """
        try:
            # Get UTXOs for fee estimation
            all_utxos = []
            for addr in from_addresses:
                utxos = self.rpc.list_unspent(self.confirmation_blocks, 9999999, [addr])
                all_utxos.extend(utxos)
            
            if not all_utxos:
                return Decimal('0.01'), False  # Default fee, cannot avoid change
            
            # Check if we can find UTXOs that avoid change
            max_fee = Decimal('0.01')
            combination = self._find_best_utxo_combination(all_utxos, amount, max_fee)
            
            if combination:
                return combination['leftover'], True
            else:
                # Estimate fee for traditional transaction with change
                try:
                    network_fee = self.rpc.estimate_fee(6)  # 6 block confirmation target
                    # Estimate transaction size: inputs * 180 + outputs * 34 + 10
                    estimated_inputs = min(3, len(all_utxos))  # Assume max 3 inputs needed
                    estimated_outputs = 2  # recipient + change
                    estimated_size = estimated_inputs * 180 + estimated_outputs * 34 + 10
                    estimated_fee = (network_fee * estimated_size) / 1000  # fee per byte
                    
                    return max(estimated_fee, Decimal('0.0001')), False
                except:
                    return Decimal('0.01'), False  # Fallback
                    
        except Exception as e:
            self.logger.error(f"Fee estimation failed: {e}")
            return Decimal('0.01'), False
    
    def consolidate_utxos(self, user: User, target_address: str = None, 
                         max_fee: Decimal = Decimal('0.01')) -> Tuple[bool, str]:
        """
        Consolidate small UTXOs into larger ones to improve future transaction efficiency.
        
        Args:
            user: User whose UTXOs to consolidate
            target_address: Address to consolidate to (uses user's primary if None)
            max_fee: Maximum fee to pay for consolidation
            
        Returns:
            (success, message_or_txid)
        """
        try:
            addresses = self.rpc.get_addresses_by_account(user.trmp_account)
            if not addresses:
                return False, "No addresses found for user"
            
            if target_address is None:
                target_address = user.trmp_address
            
            # Get all UTXOs
            all_utxos = []
            for addr in addresses:
                utxos = self.rpc.list_unspent(self.confirmation_blocks, 9999999, [addr])
                all_utxos.extend(utxos)
            
            if len(all_utxos) < 2:
                return False, "Not enough UTXOs to consolidate"
            
            # Sort by amount and consolidate smaller ones
            all_utxos.sort(key=lambda x: Decimal(str(x['amount'])))
            
            # Take up to 10 smallest UTXOs for consolidation
            utxos_to_consolidate = all_utxos[:min(10, len(all_utxos))]
            total_input = sum(Decimal(str(utxo['amount'])) for utxo in utxos_to_consolidate)
            
            if total_input <= max_fee:
                return False, f"Total UTXO value ({total_input}) is too small to consolidate"
            
            # Build consolidation transaction
            inputs = []
            for utxo in utxos_to_consolidate:
                inputs.append({
                    "txid": utxo['txid'],
                    "vout": utxo['vout']
                })
            
            # Single output (consolidation target)
            output_amount = total_input - max_fee
            outputs = {target_address: float(output_amount)}
            
            # Create and send transaction
            raw_tx = self.rpc.create_raw_transaction(inputs, outputs)
            signed_result = self.rpc.sign_raw_transaction(raw_tx)
            
            if not signed_result.get('complete', False):
                return False, "Failed to sign consolidation transaction"
            
            txid = self.rpc.send_raw_transaction(signed_result['hex'])
            
            self.logger.info(f"UTXO consolidation successful for {user.username}: {len(utxos_to_consolidate)} UTXOs -> 1 UTXO, txid: {txid}")
            return True, f"Consolidated {len(utxos_to_consolidate)} UTXOs into one. Transaction: {txid}"
            
        except Exception as e:
            self.logger.error(f"UTXO consolidation failed for {user.username}: {e}")
            return False, f"Consolidation failed: {str(e)}"