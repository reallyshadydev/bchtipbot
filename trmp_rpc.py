import requests
import json
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union


class TrumpowRPCError(Exception):
    """Custom exception for Trumpow RPC errors."""
    pass


class TrumpowRPC:
    """
    Trumpow RPC client for interacting with the Trumpow Core daemon.
    Uses the same RPC interface as Dogecoin with comprehensive support
    for raw transactions and proper UTXO management.
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
    
    # ==========================================
    # Blockchain Query Methods
    # ==========================================
    
    def get_best_block_hash(self) -> str:
        """Returns the hash of the best (tip) block in the longest blockchain."""
        return self._call_rpc("getbestblockhash")
    
    def get_block(self, blockhash: str, verbosity: int = 1) -> Union[str, Dict]:
        """
        Get block data by hash.
        
        Args:
            blockhash: Hash of the block
            verbosity: 0 for hex, 1 for detailed object, 2 with tx details
        """
        return self._call_rpc("getblock", [blockhash, verbosity])
    
    def get_blockchain_info(self) -> Dict:
        """Returns an object containing various state info regarding blockchain processing."""
        return self._call_rpc("getblockchaininfo")
    
    def get_block_count(self) -> int:
        """Returns the number of blocks in the longest blockchain."""
        return self._call_rpc("getblockcount")
    
    def get_block_hash(self, height: int) -> str:
        """Returns hash of block at given height."""
        return self._call_rpc("getblockhash", [height])
    
    def get_block_header(self, hash: str, verbose: bool = True) -> Union[str, Dict]:
        """Get block header information."""
        return self._call_rpc("getblockheader", [hash, verbose])
    
    def get_block_stats(self, hash_or_height: Union[str, int], stats: List[str] = None) -> Dict:
        """Get block statistics."""
        if stats:
            return self._call_rpc("getblockstats", [hash_or_height, stats])
        return self._call_rpc("getblockstats", [hash_or_height])
    
    def get_chain_tips(self) -> List[Dict]:
        """Return information about all known tips in the block tree."""
        return self._call_rpc("getchaintips")
    
    def get_coin_count(self, height: Optional[int] = None) -> int:
        """Returns the number of coins mined in the longest blockchain."""
        if height is not None:
            return self._call_rpc("getcoincount", [height])
        return self._call_rpc("getcoincount")
    
    def get_difficulty(self) -> float:
        """Returns the proof-of-work difficulty as a multiple of the minimum difficulty."""
        return self._call_rpc("getdifficulty")
    
    def get_txout_set_info(self) -> Dict:
        """Returns statistics about the unspent transaction output set."""
        return self._call_rpc("gettxoutsetinfo")
    
    def get_txout(self, txid: str, n: int, include_mempool: bool = True) -> Optional[Dict]:
        """Returns details about an unspent transaction output."""
        return self._call_rpc("gettxout", [txid, n, include_mempool])
    
    # ==========================================
    # Raw Transaction Methods
    # ==========================================
    
    def create_raw_transaction(self, inputs: List[Dict], outputs: Dict, locktime: int = 0) -> str:
        """
        Create a raw transaction.
        
        Args:
            inputs: List of {"txid": str, "vout": int} objects
            outputs: Dict of {address: amount} or {"data": hex_string}
            locktime: Optional locktime
            
        Returns:
            Raw transaction hex string
        """
        return self._call_rpc("createrawtransaction", [inputs, outputs, locktime])
    
    def decode_raw_transaction(self, hexstring: str) -> Dict:
        """Decode a raw transaction hex string."""
        return self._call_rpc("decoderawtransaction", [hexstring])
    
    def decode_script(self, hexstring: str) -> Dict:
        """Decode a hex-encoded script."""
        return self._call_rpc("decodescript", [hexstring])
    
    def fund_raw_transaction(self, hexstring: str, options: Dict = None) -> Dict:
        """Fund a raw transaction with inputs."""
        if options:
            return self._call_rpc("fundrawtransaction", [hexstring, options])
        return self._call_rpc("fundrawtransaction", [hexstring])
    
    def get_raw_transaction(self, txid: str, verbose: bool = False) -> Union[str, Dict]:
        """Get raw transaction data."""
        return self._call_rpc("getrawtransaction", [txid, verbose])
    
    def send_raw_transaction(self, hexstring: str, allow_high_fees: bool = False) -> str:
        """Send a raw transaction."""
        return self._call_rpc("sendrawtransaction", [hexstring, allow_high_fees])
    
    def sign_raw_transaction(self, hexstring: str, prevtxs: List[Dict] = None, 
                           privkeys: List[str] = None, sighashtype: str = "ALL") -> Dict:
        """
        Sign a raw transaction.
        
        Args:
            hexstring: Raw transaction hex
            prevtxs: Previous transaction outputs
            privkeys: Private keys for signing
            sighashtype: Signature hash type
            
        Returns:
            Dict with 'hex' (signed transaction) and 'complete' (bool)
        """
        params = [hexstring]
        if prevtxs is not None:
            params.append(prevtxs)
            if privkeys is not None:
                params.append(privkeys)
                if sighashtype != "ALL":
                    params.append(sighashtype)
        return self._call_rpc("signrawtransaction", params)
    
    # ==========================================
    # UTXO and Transaction Output Methods
    # ==========================================
    
    def list_unspent(self, minconf: int = 1, maxconf: int = 9999999, 
                    addresses: List[str] = None, include_unsafe: bool = True,
                    query_options: Dict = None) -> List[Dict]:
        """
        List unspent transaction outputs.
        
        Args:
            minconf: Minimum confirmations
            maxconf: Maximum confirmations
            addresses: Filter by addresses
            include_unsafe: Include unsafe transactions
            query_options: Additional query options
            
        Returns:
            List of unspent outputs
        """
        params = [minconf, maxconf]
        if addresses is not None:
            params.append(addresses)
            if not include_unsafe:
                params.append(include_unsafe)
                if query_options is not None:
                    params.append(query_options)
        return self._call_rpc("listunspent", params)
    
    def lock_unspent(self, unlock: bool, transactions: List[Dict] = None) -> bool:
        """
        Lock or unlock specified transaction outputs.
        
        Args:
            unlock: True to unlock, False to lock
            transactions: List of {"txid": str, "vout": int}
        """
        if transactions is None:
            transactions = []
        return self._call_rpc("lockunspent", [unlock, transactions])
    
    def list_lock_unspent(self) -> List[Dict]:
        """Returns list of temporarily unspendable outputs."""
        return self._call_rpc("listlockunspent")
    
    def get_txout_proof(self, txids: List[str], blockhash: str = None) -> str:
        """Get a hex-encoded proof that given txids are in a block."""
        if blockhash:
            return self._call_rpc("gettxoutproof", [txids, blockhash])
        return self._call_rpc("gettxoutproof", [txids])
    
    def verify_txout_proof(self, proof: str) -> List[str]:
        """Verify that a proof points to txids in a block."""
        return self._call_rpc("verifytxoutproof", [proof])
    
    # ==========================================
    # Memory Pool Methods
    # ==========================================
    
    def get_mempool_info(self) -> Dict:
        """Returns details on the active state of the TX memory pool."""
        return self._call_rpc("getmempoolinfo")
    
    def get_raw_mempool(self, verbose: bool = False) -> Union[List[str], Dict]:
        """Returns all transaction ids in memory pool."""
        return self._call_rpc("getrawmempool", [verbose])
    
    def get_mempool_entry(self, txid: str) -> Dict:
        """Returns mempool data for given transaction."""
        return self._call_rpc("getmempoolentry", [txid])
    
    def get_mempool_ancestors(self, txid: str, verbose: bool = False) -> Union[List[str], Dict]:
        """Get all in-mempool ancestors of a transaction."""
        return self._call_rpc("getmempoolancestors", [txid, verbose])
    
    def get_mempool_descendants(self, txid: str, verbose: bool = False) -> Union[List[str], Dict]:
        """Get all in-mempool descendants of a transaction."""
        return self._call_rpc("getmempooldescendants", [txid, verbose])
    
    # ==========================================
    # Fee Estimation Methods
    # ==========================================
    
    def estimate_fee(self, nblocks: int = 6) -> Decimal:
        """Estimate the fee per kilobyte needed for a transaction."""
        try:
            result = self._call_rpc("estimatefee", [nblocks])
            return Decimal(str(result)) if result != -1 else Decimal("0.001")
        except TrumpowRPCError:
            # Fallback fee if estimation is not available
            return Decimal("0.001")
    
    def estimate_smart_fee(self, nblocks: int, estimate_mode: str = "CONSERVATIVE") -> Dict:
        """Estimate smart fee for confirmation within nblocks."""
        return self._call_rpc("estimatesmartfee", [nblocks, estimate_mode])
    
    def estimate_priority(self, nblocks: int) -> float:
        """Estimate the priority needed for a transaction."""
        return self._call_rpc("estimatepriority", [nblocks])
    
    def estimate_smart_priority(self, nblocks: int) -> Dict:
        """Estimate smart priority for confirmation within nblocks."""
        return self._call_rpc("estimatesmartpriority", [nblocks])
    
    # ==========================================
    # Mining Methods
    # ==========================================
    
    def get_mining_info(self) -> Dict:
        """Returns a json object containing mining-related information."""
        return self._call_rpc("getmininginfo")
    
    def get_network_hashps(self, nblocks: int = 120, height: int = -1) -> float:
        """Returns the estimated network hashes per second."""
        return self._call_rpc("getnetworkhashps", [nblocks, height])
    
    def get_block_template(self, template_request: Dict = None) -> Dict:
        """Get block template for mining."""
        if template_request:
            return self._call_rpc("getblocktemplate", [template_request])
        return self._call_rpc("getblocktemplate")
    
    def submit_block(self, hexdata: str, jsonparametersobject: Dict = None) -> str:
        """Submit a new block to the network."""
        if jsonparametersobject:
            return self._call_rpc("submitblock", [hexdata, jsonparametersobject])
        return self._call_rpc("submitblock", [hexdata])
    
    def generate(self, nblocks: int, maxtries: int = 1000000, auxpow: bool = False) -> List[str]:
        """Generate blocks immediately (for testing)."""
        return self._call_rpc("generate", [nblocks, maxtries, auxpow])
    
    def generate_to_address(self, nblocks: int, address: str, maxtries: int = 1000000, auxpow: bool = False) -> List[str]:
        """Generate blocks to a specific address."""
        return self._call_rpc("generatetoaddress", [nblocks, address, maxtries, auxpow])
    
    # ==========================================
    # Wallet Methods (Legacy Account System)
    # ==========================================
    
    def get_balance(self, account: str = "*", minconf: int = 1) -> Decimal:
        """Get the balance for an account."""
        result = self._call_rpc("getbalance", [account, minconf])
        return Decimal(str(result))
    
    def get_new_address(self, account: str = "") -> str:
        """Generate a new TRMP address for the specified account."""
        return self._call_rpc("getnewaddress", [account])
    
    def get_raw_change_address(self) -> str:
        """Returns a new address for receiving change (raw transactions only)."""
        return self._call_rpc("getrawchangeaddress")
    
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
    
    def send_many(self, from_account: str, amounts: Dict[str, Decimal], 
                  minconf: int = 1, comment: str = "", 
                  subtract_fee_from_addresses: List[str] = None) -> str:
        """Send to multiple addresses at once."""
        amounts_str = {addr: f"{amount:.8f}" for addr, amount in amounts.items()}
        params = [from_account, amounts_str, minconf, comment]
        if subtract_fee_from_addresses:
            params.append(subtract_fee_from_addresses)
        return self._call_rpc("sendmany", params)
    
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
    
    def list_accounts(self, minconf: int = 1, include_watchonly: bool = False) -> Dict[str, Decimal]:
        """List all accounts and their balances."""
        result = self._call_rpc("listaccounts", [minconf, include_watchonly])
        return {account: Decimal(str(balance)) for account, balance in result.items()}
    
    def list_address_groupings(self) -> List[List[List]]:
        """Lists groups of addresses which have had their common ownership made public."""
        return self._call_rpc("listaddressgroupings")
    
    def list_received_by_account(self, minconf: int = 1, include_empty: bool = False, 
                               include_watchonly: bool = False) -> List[Dict]:
        """List received amounts by account."""
        return self._call_rpc("listreceivedbyaccount", [minconf, include_empty, include_watchonly])
    
    def list_received_by_address(self, minconf: int = 1, include_empty: bool = False,
                               include_watchonly: bool = False) -> List[Dict]:
        """List received amounts by address."""
        return self._call_rpc("listreceivedbyaddress", [minconf, include_empty, include_watchonly])
    
    def list_transactions(self, account: str = "*", count: int = 10, 
                         skip: int = 0, include_watchonly: bool = False) -> List[Dict]:
        """List recent transactions for an account."""
        return self._call_rpc("listtransactions", [account, count, skip, include_watchonly])
    
    def list_since_block(self, blockhash: str = None, target_confirmations: int = 1,
                        include_watchonly: bool = False) -> Dict:
        """Get all transactions since block."""
        params = []
        if blockhash:
            params.append(blockhash)
            params.append(target_confirmations)
            params.append(include_watchonly)
        return self._call_rpc("listsinceblock", params)
    
    def get_transaction(self, txid: str, include_watchonly: bool = False) -> Dict:
        """Get detailed information about a transaction."""
        return self._call_rpc("gettransaction", [txid, include_watchonly])
    
    def get_unconfirmed_balance(self) -> Decimal:
        """Returns the server's total unconfirmed balance."""
        result = self._call_rpc("getunconfirmedbalance")
        return Decimal(str(result))
    
    # ==========================================
    # Address and Key Management
    # ==========================================
    
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
    
    def dump_privkey(self, address: str) -> str:
        """Dump the private key for an address."""
        return self._call_rpc("dumpprivkey", [address])
    
    def import_privkey(self, privkey: str, label: str = "", rescan: bool = True) -> None:
        """Import a private key."""
        self._call_rpc("importprivkey", [privkey, label, rescan])
    
    def import_address(self, address: str, label: str = "", rescan: bool = True, 
                      p2sh: bool = False) -> None:
        """Import an address."""
        self._call_rpc("importaddress", [address, label, rescan, p2sh])
    
    def import_pubkey(self, pubkey: str, label: str = "", rescan: bool = True) -> None:
        """Import a public key."""
        self._call_rpc("importpubkey", [pubkey, label, rescan])
    
    def sign_message(self, address: str, message: str) -> str:
        """Sign a message with the private key of an address."""
        return self._call_rpc("signmessage", [address, message])
    
    def verify_message(self, address: str, signature: str, message: str) -> bool:
        """Verify a signed message."""
        return self._call_rpc("verifymessage", [address, signature, message])
    
    def sign_message_with_privkey(self, privkey: str, message: str) -> str:
        """Sign a message with a private key."""
        return self._call_rpc("signmessagewithprivkey", [privkey, message])
    
    # ==========================================
    # Wallet Management
    # ==========================================
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information."""
        return self._call_rpc("getwalletinfo")
    
    def backup_wallet(self, destination: str) -> None:
        """Backup the wallet."""
        self._call_rpc("backupwallet", [destination])
    
    def dump_wallet(self, filename: str) -> None:
        """Dump wallet to a file."""
        self._call_rpc("dumpwallet", [filename])
    
    def import_wallet(self, filename: str) -> None:
        """Import a wallet from a file."""
        self._call_rpc("importwallet", [filename])
    
    def encrypt_wallet(self, passphrase: str) -> None:
        """Encrypt the wallet with a passphrase."""
        self._call_rpc("encryptwallet", [passphrase])
    
    def set_tx_fee(self, amount: Decimal) -> bool:
        """Set the transaction fee."""
        return self._call_rpc("settxfee", [f"{amount:.8f}"])
    
    def keypool_refill(self, newsize: int = 100) -> None:
        """Refill the keypool."""
        self._call_rpc("keypoolrefill", [newsize])
    
    # ==========================================
    # Network Information and Control
    # ==========================================
    
    def get_info(self) -> Dict:
        """Get general information about the node and network (DEPRECATED)."""
        return self._call_rpc("getinfo")
    
    def get_memory_info(self) -> Dict:
        """Returns an object containing information about memory usage."""
        return self._call_rpc("getmemoryinfo")
    
    def get_network_info(self) -> Dict:
        """Get network-related information."""
        return self._call_rpc("getnetworkinfo")
    
    def get_connection_count(self) -> int:
        """Get the number of connections to other nodes."""
        return self._call_rpc("getconnectioncount")
    
    def get_net_totals(self) -> Dict:
        """Returns information about network traffic."""
        return self._call_rpc("getnettotals")
    
    def get_peer_info(self) -> List[Dict]:
        """Returns data about each connected network node."""
        return self._call_rpc("getpeerinfo")
    
    def add_node(self, node: str, command: str) -> None:
        """Add, remove, or try connecting to a node."""
        self._call_rpc("addnode", [node, command])
    
    def disconnect_node(self, address: str) -> None:
        """Disconnect from a node."""
        self._call_rpc("disconnectnode", [address])
    
    def get_added_node_info(self, node: str = None) -> Union[List[Dict], Dict]:
        """Get information about added nodes."""
        if node:
            return self._call_rpc("getaddednodeinfo", [node])
        return self._call_rpc("getaddednodeinfo")
    
    def list_banned(self) -> List[Dict]:
        """List all banned IPs/Subnets."""
        return self._call_rpc("listbanned")
    
    def set_ban(self, subnet: str, command: str, bantime: int = 86400, absolute: bool = False) -> None:
        """Set or remove a ban."""
        self._call_rpc("setban", [subnet, command, bantime, absolute])
    
    def clear_banned(self) -> None:
        """Clear all banned IPs."""
        self._call_rpc("clearbanned")
    
    def set_network_active(self, state: bool) -> None:
        """Enable/disable all P2P network activity."""
        self._call_rpc("setnetworkactive", [state])
    
    def set_max_connections(self, count: int) -> bool:
        """Set maximum number of connections."""
        return self._call_rpc("setmaxconnections", [count])
    
    # ==========================================
    # Utility Methods
    # ==========================================
    
    def ping(self) -> None:
        """Send a ping to all connected nodes."""
        self._call_rpc("ping")
    
    def help(self, command: str = None) -> str:
        """Get help for RPC commands."""
        if command:
            return self._call_rpc("help", [command])
        return self._call_rpc("help")
    
    def stop(self) -> str:
        """Stop the Trumpow server."""
        return self._call_rpc("stop")
    
    def verify_chain(self, checklevel: int = 3, nblocks: int = 6) -> bool:
        """Verify blockchain database."""
        return self._call_rpc("verifychain", [checklevel, nblocks])
    
    def prune_blockchain(self, height: int) -> int:
        """Prune blockchain up to specified height."""
        return self._call_rpc("pruneblockchain", [height])
    
    def test_connection(self) -> bool:
        """Test if the connection to the Trumpow daemon is working."""
        try:
            self.get_blockchain_info()
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
    
    # ==========================================
    # Advanced Transaction Building Methods
    # ==========================================
    
    def build_transaction(self, from_address: str, to_address: str, amount: Decimal, 
                         fee_rate: Decimal = None) -> Dict:
        """
        Build a raw transaction from scratch using UTXOs.
        This avoids change address issues by manually selecting UTXOs.
        
        Args:
            from_address: Source address
            to_address: Destination address  
            amount: Amount to send
            fee_rate: Fee rate in TRMP/kB (optional)
            
        Returns:
            Dict with transaction details and hex
        """
        # Get UTXOs for the from_address
        unspent = self.list_unspent(1, 9999999, [from_address])
        
        if not unspent:
            raise TrumpowRPCError(f"No unspent outputs for address {from_address}")
        
        # Calculate fee rate
        if fee_rate is None:
            fee_rate = self.estimate_fee(6)
        
        # Select UTXOs (simple first-fit algorithm)
        selected_utxos = []
        total_input = Decimal('0')
        
        for utxo in sorted(unspent, key=lambda x: x['amount'], reverse=True):
            selected_utxos.append({
                'txid': utxo['txid'],
                'vout': utxo['vout']
            })
            total_input += Decimal(str(utxo['amount']))
            
            # Estimate transaction size (roughly 180 bytes per input + 34 bytes per output + 10 bytes overhead)
            tx_size = len(selected_utxos) * 180 + 2 * 34 + 10
            estimated_fee = fee_rate * (tx_size / 1000)  # Fee per kB
            
            if total_input >= amount + estimated_fee:
                break
        
        if total_input < amount:
            raise TrumpowRPCError(f"Insufficient funds: have {total_input}, need {amount}")
        
        # Calculate actual fee and change
        tx_size = len(selected_utxos) * 180 + 2 * 34 + 10
        actual_fee = fee_rate * (tx_size / 1000)
        change = total_input - amount - actual_fee
        
        # Build outputs
        outputs = {to_address: float(amount)}
        
        # Add change output if significant (avoid dust)
        min_change = Decimal('0.00001')  # 1000 satoshis
        if change > min_change:
            change_address = self.get_raw_change_address()
            outputs[change_address] = float(change)
        else:
            # Add dust to fee
            actual_fee += change
        
        # Create raw transaction
        raw_tx = self.create_raw_transaction(selected_utxos, outputs)
        
        # Sign the transaction
        signed_result = self.sign_raw_transaction(raw_tx)
        
        if not signed_result.get('complete', False):
            raise TrumpowRPCError("Failed to sign transaction")
        
        return {
            'hex': signed_result['hex'],
            'txid': None,  # Will be set when broadcast
            'inputs': selected_utxos,
            'outputs': outputs,
            'fee': actual_fee,
            'total_input': total_input
        }
    
    def send_raw_transaction_safe(self, from_address: str, to_address: str, 
                                 amount: Decimal, fee_rate: Decimal = None) -> str:
        """
        Build and send a raw transaction safely.
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount to send
            fee_rate: Fee rate in TRMP/kB (optional)
            
        Returns:
            Transaction ID
        """
        # Build the transaction
        tx_data = self.build_transaction(from_address, to_address, amount, fee_rate)
        
        # Broadcast the transaction
        txid = self.send_raw_transaction(tx_data['hex'])
        
        return txid
    
    def create_multisig(self, nrequired: int, keys: List[str]) -> Dict:
        """Create a multisig address."""
        return self._call_rpc("createmultisig", [nrequired, keys])
    
    def add_multisig_address(self, nrequired: int, keys: List[str], account: str = "") -> str:
        """Add a multisig address to the wallet."""
        return self._call_rpc("addmultisigaddress", [nrequired, keys, account])