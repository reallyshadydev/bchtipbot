import os
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class DogecoinClient:
    def __init__(self):
        self.rpc_host = os.getenv('DOGECOIN_RPC_HOST', '127.0.0.1')
        self.rpc_port = os.getenv('DOGECOIN_RPC_PORT', '22555')
        self.rpc_user = os.getenv('DOGECOIN_RPC_USER')
        self.rpc_password = os.getenv('DOGECOIN_RPC_PASSWORD')
        
        if not self.rpc_user or not self.rpc_password:
            raise ValueError("DOGECOIN_RPC_USER and DOGECOIN_RPC_PASSWORD must be set")
        
        self.rpc_url = f"http://{self.rpc_user}:{self.rpc_password}@{self.rpc_host}:{self.rpc_port}"
        self.rpc_connection = AuthServiceProxy(self.rpc_url)
    
    def get_new_address(self, label=""):
        """Generate a new Dogecoin address"""
        try:
            return self.rpc_connection.getnewaddress(label)
        except JSONRPCException as e:
            logger.error(f"Error generating new address: {e}")
            raise
    
    def get_balance(self, address=None, confirmations=1):
        """Get balance for an address or wallet"""
        try:
            if address:
                # Get balance for specific address
                unspent = self.rpc_connection.listunspent(confirmations, 9999999, [address])
                return sum(Decimal(str(utxo['amount'])) for utxo in unspent)
            else:
                # Get wallet balance
                return Decimal(str(self.rpc_connection.getbalance()))
        except JSONRPCException as e:
            logger.error(f"Error getting balance: {e}")
            return Decimal('0')
    
    def send_to_address(self, address, amount, comment=""):
        """Send Dogecoin to an address"""
        try:
            # Convert amount to Decimal for precision
            amount = Decimal(str(amount))
            txid = self.rpc_connection.sendtoaddress(str(address), float(amount), comment)
            return txid
        except JSONRPCException as e:
            logger.error(f"Error sending to address: {e}")
            raise
    
    def get_transaction(self, txid):
        """Get transaction details"""
        try:
            return self.rpc_connection.gettransaction(txid)
        except JSONRPCException as e:
            logger.error(f"Error getting transaction: {e}")
            return None
    
    def validate_address(self, address):
        """Validate a Dogecoin address"""
        try:
            result = self.rpc_connection.validateaddress(address)
            return result.get('isvalid', False)
        except JSONRPCException as e:
            logger.error(f"Error validating address: {e}")
            return False
    
    def get_network_info(self):
        """Get network information"""
        try:
            return self.rpc_connection.getnetworkinfo()
        except JSONRPCException as e:
            logger.error(f"Error getting network info: {e}")
            return None
    
    def import_address(self, address, label="", rescan=False):
        """Import an address to watch-only"""
        try:
            return self.rpc_connection.importaddress(address, label, rescan)
        except JSONRPCException as e:
            logger.error(f"Error importing address: {e}")
            raise
    
    def list_received_by_address(self, min_confirmations=1, include_empty=True):
        """List amounts received by each address"""
        try:
            return self.rpc_connection.listreceivedbyaddress(min_confirmations, include_empty)
        except JSONRPCException as e:
            logger.error(f"Error listing received by address: {e}")
            return []


# Global client instance
dogecoin_client = None

def get_dogecoin_client():
    """Get or create the global Dogecoin client instance"""
    global dogecoin_client
    if dogecoin_client is None:
        dogecoin_client = DogecoinClient()
    return dogecoin_client