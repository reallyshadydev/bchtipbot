import logging
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
from typing import Optional, Dict, Any
from settings import TRMP_RPC_HOST, TRMP_RPC_PORT, TRMP_RPC_USER, TRMP_RPC_PASSWORD, TRMP_RPC_WALLET

logger = logging.getLogger(__name__)


class TRMPWallet:
    """
    TRMP wallet interface using Dogecoin RPC
    """
    
    def __init__(self):
        self.rpc_url = f"http://{TRMP_RPC_USER}:{TRMP_RPC_PASSWORD}@{TRMP_RPC_HOST}:{TRMP_RPC_PORT}"
        self.rpc_connection = None
        self._connect()
    
    def _connect(self):
        """Establish RPC connection"""
        try:
            self.rpc_connection = AuthServiceProxy(self.rpc_url)
            # Test the connection
            self.rpc_connection.getblockchaininfo()
            logger.info("Successfully connected to TRMP node")
        except Exception as e:
            logger.error(f"Failed to connect to TRMP node: {e}")
            raise
    
    def _execute_rpc(self, method: str, *args) -> Any:
        """Execute RPC command with error handling"""
        try:
            return getattr(self.rpc_connection, method)(*args)
        except JSONRPCException as e:
            logger.error(f"RPC error executing {method}: {e}")
            raise
        except Exception as e:
            logger.error(f"Connection error executing {method}: {e}")
            # Try to reconnect
            self._connect()
            return getattr(self.rpc_connection, method)(*args)
    
    def create_address(self, label: str = "") -> str:
        """Create a new TRMP address"""
        try:
            address = self._execute_rpc("getnewaddress", label)
            logger.info(f"Created new address: {address}")
            return address
        except Exception as e:
            logger.error(f"Failed to create address: {e}")
            raise
    
    def get_balance(self, address: Optional[str] = None, confirmations: int = 1) -> Decimal:
        """Get balance for an address or entire wallet"""
        try:
            if address:
                # Get balance for specific address
                unspent = self._execute_rpc("listunspent", confirmations, 9999999, [address])
                balance = sum(Decimal(str(utxo['amount'])) for utxo in unspent)
            else:
                # Get total wallet balance
                balance = Decimal(str(self._execute_rpc("getbalance", "*", confirmations)))
            
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return Decimal('0')
    
    def send_transaction(self, to_address: str, amount: Decimal, from_address: Optional[str] = None) -> str:
        """Send TRMP to an address"""
        try:
            # Convert amount to float for RPC (Dogecoin core expects float)
            amount_float = float(amount)
            
            if from_address:
                # Send from specific address (more complex, requires manual UTXO selection)
                return self._send_from_address(from_address, to_address, amount_float)
            else:
                # Simple send from wallet
                txid = self._execute_rpc("sendtoaddress", to_address, amount_float)
                logger.info(f"Sent {amount} TRMP to {to_address}, txid: {txid}")
                return txid
                
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            raise
    
    def _send_from_address(self, from_address: str, to_address: str, amount: float) -> str:
        """Send from a specific address using manual UTXO selection"""
        try:
            # Get unspent outputs for the from_address
            unspent = self._execute_rpc("listunspent", 1, 9999999, [from_address])
            
            if not unspent:
                raise ValueError(f"No unspent outputs found for address {from_address}")
            
            # Calculate total available
            total_available = sum(Decimal(str(utxo['amount'])) for utxo in unspent)
            
            if total_available < Decimal(str(amount)):
                raise ValueError(f"Insufficient balance. Available: {total_available}, Required: {amount}")
            
            # Prepare inputs
            inputs = []
            input_amount = Decimal('0')
            
            for utxo in unspent:
                inputs.append({
                    "txid": utxo['txid'],
                    "vout": utxo['vout']
                })
                input_amount += Decimal(str(utxo['amount']))
                
                # Stop when we have enough (with some buffer for fees)
                if input_amount >= Decimal(str(amount)) + Decimal('0.01'):
                    break
            
            # Prepare outputs
            outputs = {to_address: amount}
            
            # Calculate change
            fee = Decimal('0.01')  # 0.01 TRMP fee
            change = input_amount - Decimal(str(amount)) - fee
            
            if change > Decimal('0.001'):  # Only add change output if significant
                outputs[from_address] = float(change)
            
            # Create raw transaction
            raw_tx = self._execute_rpc("createrawtransaction", inputs, outputs)
            
            # Sign transaction
            signed_tx = self._execute_rpc("signrawtransaction", raw_tx)
            
            if not signed_tx.get('complete'):
                raise ValueError("Failed to sign transaction")
            
            # Send transaction
            txid = self._execute_rpc("sendrawtransaction", signed_tx['hex'])
            logger.info(f"Sent {amount} TRMP from {from_address} to {to_address}, txid: {txid}")
            return txid
            
        except Exception as e:
            logger.error(f"Failed to send from specific address: {e}")
            raise
    
    def validate_address(self, address: str) -> bool:
        """Validate if an address is valid"""
        try:
            result = self._execute_rpc("validateaddress", address)
            return result.get('isvalid', False)
        except Exception as e:
            logger.error(f"Failed to validate address {address}: {e}")
            return False
    
    def get_transaction_info(self, txid: str) -> Dict[str, Any]:
        """Get transaction information"""
        try:
            return self._execute_rpc("gettransaction", txid)
        except Exception as e:
            logger.error(f"Failed to get transaction info for {txid}: {e}")
            return {}
    
    def get_new_address_for_user(self, username: str) -> str:
        """Create a new address labeled with username"""
        return self.create_address(f"tipbot_user_{username}")
    
    def import_address(self, address: str, label: str = "", rescan: bool = False):
        """Import an address for watching"""
        try:
            self._execute_rpc("importaddress", address, label, rescan)
            logger.info(f"Imported address: {address}")
        except Exception as e:
            logger.error(f"Failed to import address {address}: {e}")
            raise


# Global wallet instance
wallet = TRMPWallet()