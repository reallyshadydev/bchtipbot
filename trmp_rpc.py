import requests
import json
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional


class TrumpowRPCError(Exception):
    """Custom exception for Trumpow RPC errors."""
    pass


class TrumpowRPC:
    """
    Trumpow RPC client for interacting with the Trumpow Core daemon.
    Uses the same RPC interface as Dogecoin.
    """
    
    def __init__(self, host: str, port: int, user: str, password: str, wallet: str = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.wallet = wallet
        self.url = f"http://{host}:{port}"
        if wallet:
            self.url += f"/wallet/{wallet}"
        
        self.logger = logging.getLogger(__name__)
    
    def _call_rpc(self, method: str, params: List[Any] = None) -> Any:
        """
        Make an RPC call to the Trumpow daemon.
        
        Args:
            method: RPC method name
            params: List of parameters for the method
            
        Returns:
            Result from the RPC call
            
        Raises:
            TrumpowRPCError: If the RPC call fails
        """
        if params is None:
            params = []
            
        payload = {
            "jsonrpc": "1.0",
            "id": "tipbot",
            "method": method,
            "params": params
        }
        
        try:
            response = requests.post(
                self.url,
                json=payload,
                auth=(self.user, self.password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('error'):
                error_msg = result['error'].get('message', 'Unknown RPC error')
                self.logger.error(f"RPC error: {error_msg}")
                raise TrumpowRPCError(f"RPC error: {error_msg}")
                
            return result.get('result')
            
        except requests.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise TrumpowRPCError(f"Request error: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            raise TrumpowRPCError(f"JSON decode error: {e}")
    
    # Wallet Methods
    def get_balance(self, account: str = "*", minconf: int = 1) -> Decimal:
        """Get the balance for an account."""
        result = self._call_rpc("getbalance", [account, minconf])
        return Decimal(str(result))
    
    def get_new_address(self, account: str = "") -> str:
        """Generate a new TRMP address for the specified account."""
        return self._call_rpc("getnewaddress", [account])
    
    def get_account_address(self, account: str) -> str:
        """Get the current TRMP address for receiving payments to this account."""
        return self._call_rpc("getaccountaddress", [account])
    
    def send_to_address(self, address: str, amount: Decimal, comment: str = "", 
                       comment_to: str = "", subtract_fee: bool = False) -> str:
        """Send TRMP to a specified address."""
        amount_str = f"{amount:.8f}"
        return self._call_rpc("sendtoaddress", [address, amount_str, comment, comment_to, subtract_fee])
    
    def send_from(self, from_account: str, to_address: str, amount: Decimal, 
                  minconf: int = 1, comment: str = "", comment_to: str = "") -> str:
        """Send TRMP from a specific account to an address."""
        amount_str = f"{amount:.8f}"
        return self._call_rpc("sendfrom", [from_account, to_address, amount_str, minconf, comment, comment_to])
    
    def move(self, from_account: str, to_account: str, amount: Decimal, 
             minconf: int = 1, comment: str = "") -> bool:
        """Move TRMP from one account to another."""
        amount_str = f"{amount:.8f}"
        return self._call_rpc("move", [from_account, to_account, amount_str, minconf, comment])
    
    def get_received_by_account(self, account: str, minconf: int = 1) -> Decimal:
        """Get the total amount received by an account."""
        result = self._call_rpc("getreceivedbyaccount", [account, minconf])
        return Decimal(str(result))
    
    def get_received_by_address(self, address: str, minconf: int = 1) -> Decimal:
        """Get the total amount received by an address."""
        result = self._call_rpc("getreceivedbyaddress", [address, minconf])
        return Decimal(str(result))
    
    def list_accounts(self, minconf: int = 1) -> Dict[str, Decimal]:
        """List all accounts and their balances."""
        result = self._call_rpc("listaccounts", [minconf])
        return {account: Decimal(str(balance)) for account, balance in result.items()}
    
    def list_transactions(self, account: str = "*", count: int = 10, 
                         skip: int = 0, include_watchonly: bool = False) -> List[Dict]:
        """List recent transactions for an account."""
        return self._call_rpc("listtransactions", [account, count, skip, include_watchonly])
    
    def get_transaction(self, txid: str, include_watchonly: bool = False) -> Dict:
        """Get detailed information about a transaction."""
        return self._call_rpc("gettransaction", [txid, include_watchonly])
    
    def validate_address(self, address: str) -> Dict:
        """Validate a TRMP address."""
        return self._call_rpc("validateaddress", [address])
    
    def set_account(self, address: str, account: str) -> None:
        """Set the account associated with an address."""
        self._call_rpc("setaccount", [address, account])
    
    def get_account(self, address: str) -> str:
        """Get the account associated with an address."""
        return self._call_rpc("getaccount", [address])
    
    def get_addresses_by_account(self, account: str) -> List[str]:
        """Get all addresses for an account."""
        return self._call_rpc("getaddressesbyaccount", [account])
    
    # Network and Node Information
    def get_info(self) -> Dict:
        """Get general information about the node and network."""
        return self._call_rpc("getinfo")
    
    def get_network_info(self) -> Dict:
        """Get network-related information."""
        return self._call_rpc("getnetworkinfo")
    
    def get_blockchain_info(self) -> Dict:
        """Get blockchain information."""
        return self._call_rpc("getblockchaininfo")
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information."""
        return self._call_rpc("getwalletinfo")
    
    def get_connection_count(self) -> int:
        """Get the number of connections to other nodes."""
        return self._call_rpc("getconnectioncount")
    
    def get_block_count(self) -> int:
        """Get the current block height."""
        return self._call_rpc("getblockcount")
    
    def get_difficulty(self) -> float:
        """Get the current mining difficulty."""
        return self._call_rpc("getdifficulty")
    
    # Transaction Methods
    def get_raw_transaction(self, txid: str, verbose: bool = False) -> str:
        """Get raw transaction data."""
        return self._call_rpc("getrawtransaction", [txid, verbose])
    
    def send_raw_transaction(self, hex_string: str, allow_high_fees: bool = False) -> str:
        """Send a raw transaction."""
        return self._call_rpc("sendrawtransaction", [hex_string, allow_high_fees])
    
    def estimate_fee(self, nblocks: int = 6) -> Decimal:
        """Estimate the fee per kilobyte needed for a transaction."""
        result = self._call_rpc("estimatefee", [nblocks])
        return Decimal(str(result)) if result != -1 else Decimal("0.001")
    
    # Utility Methods
    def ping(self) -> None:
        """Send a ping to all connected nodes."""
        self._call_rpc("ping")
    
    def test_connection(self) -> bool:
        """Test if the connection to the Trumpow daemon is working."""
        try:
            self.get_info()
            return True
        except TrumpowRPCError:
            return False
    
    def create_account_if_not_exists(self, account: str) -> str:
        """Create an account if it doesn't exist and return its address."""
        try:
            # Try to get existing address for the account
            address = self.get_account_address(account)
        except TrumpowRPCError:
            # Account doesn't exist, create a new address
            address = self.get_new_address(account)
            self.set_account(address, account)
        
        return address