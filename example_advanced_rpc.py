#!/usr/bin/env python3
"""
Example script demonstrating advanced Trumpow RPC capabilities.

This script shows how to use the enhanced TrumpowRPC client with:
- Raw transaction building and signing
- UTXO management and analysis
- Advanced wallet management
- Proper transaction construction to avoid change address issues

Usage:
    python example_advanced_rpc.py

Note: Make sure to configure your RPC credentials before running.
"""

import os
import sys
import logging
from decimal import Decimal
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trmp_rpc import TrumpowRPC, TrumpowRPCError
from wallet_manager import AdvancedWalletManager
from database import DatabaseManager


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('advanced_rpc_example.log')
        ]
    )


def demonstrate_basic_rpc_methods(rpc: TrumpowRPC):
    """Demonstrate basic RPC methods."""
    print("\n" + "="*50)
    print("BASIC RPC METHODS DEMONSTRATION")
    print("="*50)
    
    try:
        # Network and blockchain info
        print("\n--- Network Information ---")
        network_info = rpc.get_network_info()
        print(f"Protocol Version: {network_info.get('protocolversion', 'Unknown')}")
        print(f"Connections: {network_info.get('connections', 0)}")
        print(f"Network Active: {network_info.get('networkactive', False)}")
        
        blockchain_info = rpc.get_blockchain_info()
        print(f"Current Block Height: {blockchain_info.get('blocks', 0)}")
        print(f"Best Block Hash: {blockchain_info.get('bestblockhash', 'Unknown')}")
        print(f"Difficulty: {blockchain_info.get('difficulty', 0)}")
        
        # Wallet info
        print("\n--- Wallet Information ---")
        wallet_info = rpc.get_wallet_info()
        print(f"Wallet Version: {wallet_info.get('walletversion', 'Unknown')}")
        print(f"Balance: {wallet_info.get('balance', 0)} TRMP")
        print(f"Unconfirmed Balance: {wallet_info.get('unconfirmed_balance', 0)} TRMP")
        print(f"Transaction Count: {wallet_info.get('txcount', 0)}")
        
        # Memory pool info
        print("\n--- Memory Pool Information ---")
        mempool_info = rpc.get_mempool_info()
        print(f"Mempool Size: {mempool_info.get('size', 0)} transactions")
        print(f"Mempool Usage: {mempool_info.get('usage', 0)} bytes")
        print(f"Min Fee: {mempool_info.get('mempoolminfee', 0)} TRMP/kB")
        
    except TrumpowRPCError as e:
        print(f"Error in basic RPC demonstration: {e}")


def demonstrate_utxo_management(rpc: TrumpowRPC):
    """Demonstrate UTXO management capabilities."""
    print("\n" + "="*50)
    print("UTXO MANAGEMENT DEMONSTRATION")
    print("="*50)
    
    try:
        # List unspent outputs
        print("\n--- Unspent Transaction Outputs ---")
        unspent = rpc.list_unspent(1, 9999999)  # Confirmed UTXOs only
        
        if unspent:
            print(f"Found {len(unspent)} confirmed UTXOs:")
            total_value = Decimal('0')
            
            for i, utxo in enumerate(unspent[:10]):  # Show first 10
                amount = Decimal(str(utxo['amount']))
                total_value += amount
                print(f"  {i+1}. {utxo['txid'][:16]}...:{utxo['vout']} - {amount} TRMP ({utxo['confirmations']} conf)")
            
            if len(unspent) > 10:
                remaining_value = sum(Decimal(str(u['amount'])) for u in unspent[10:])
                total_value += remaining_value
                print(f"  ... and {len(unspent)-10} more UTXOs")
            
            print(f"Total UTXO Value: {total_value} TRMP")
            
            # UTXO statistics
            amounts = [Decimal(str(u['amount'])) for u in unspent]
            print(f"Largest UTXO: {max(amounts)} TRMP")
            print(f"Smallest UTXO: {min(amounts)} TRMP")
            print(f"Average UTXO: {total_value / len(unspent)} TRMP")
            
            # Check for dust
            dust_threshold = Decimal('0.001')
            dust_count = len([a for a in amounts if a < dust_threshold])
            if dust_count > 0:
                print(f"Dust UTXOs (< {dust_threshold} TRMP): {dust_count}")
        else:
            print("No confirmed UTXOs found")
        
        # Check locked UTXOs
        print("\n--- Locked UTXOs ---")
        locked = rpc.list_lock_unspent()
        if locked:
            print(f"Found {len(locked)} locked UTXOs:")
            for lock in locked:
                print(f"  {lock['txid'][:16]}...:{lock['vout']}")
        else:
            print("No locked UTXOs")
            
    except TrumpowRPCError as e:
        print(f"Error in UTXO demonstration: {e}")


def demonstrate_raw_transactions(rpc: TrumpowRPC):
    """Demonstrate raw transaction capabilities."""
    print("\n" + "="*50)
    print("RAW TRANSACTION DEMONSTRATION")
    print("="*50)
    
    try:
        print("\n--- Fee Estimation ---")
        # Estimate fees for different confirmation targets
        for blocks in [1, 3, 6, 12]:
            try:
                fee = rpc.estimate_fee(blocks)
                print(f"Fee for {blocks} block confirmation: {fee} TRMP/kB")
            except:
                print(f"Fee estimation for {blocks} blocks: Not available")
        
        print("\n--- Raw Transaction Building Example ---")
        print("(This example shows the process without actually sending)")
        
        # Get a sample address for demonstration
        try:
            sample_address = rpc.get_new_address("example")
            print(f"Generated sample address: {sample_address}")
            
            # Show how to validate an address
            addr_info = rpc.validate_address(sample_address)
            print(f"Address valid: {addr_info.get('isvalid', False)}")
            print(f"Address type: {addr_info.get('type', 'Unknown')}")
            
        except TrumpowRPCError as e:
            print(f"Address generation failed: {e}")
        
        print("\n--- Transaction Template Creation ---")
        # Demonstrate how to create a transaction template
        sample_inputs = [
            {"txid": "0123456789abcdef" * 4, "vout": 0}
        ]
        sample_outputs = {
            "DTmYzGZtkkTv4kSKCnYbLFSMeYSzKPKHs6": 1.0  # Example address
        }
        
        try:
            # This will fail because the inputs don't exist, but shows the process
            print("Creating transaction template...")
            print(f"Inputs: {sample_inputs}")
            print(f"Outputs: {sample_outputs}")
            # raw_tx = rpc.create_raw_transaction(sample_inputs, sample_outputs)
            # print(f"Raw transaction created: {raw_tx[:50]}...")
        except Exception as e:
            print(f"Template creation (expected to fail): {e}")
            
    except TrumpowRPCError as e:
        print(f"Error in raw transaction demonstration: {e}")


def demonstrate_advanced_wallet_manager():
    """Demonstrate the AdvancedWalletManager capabilities."""
    print("\n" + "="*50)
    print("ADVANCED WALLET MANAGER DEMONSTRATION")
    print("="*50)
    
    # Note: This is a demonstration of the API, not actual usage
    # as it requires a proper database setup
    
    print("\n--- Advanced Wallet Manager Features ---")
    print("✓ UTXO-based balance calculation")
    print("✓ Raw transaction building for withdrawals")
    print("✓ UTXO consolidation to reduce fragmentation")
    print("✓ Detailed UTXO analysis and recommendations")
    print("✓ Fallback to standard transactions if raw fails")
    print("✓ Advanced fee estimation and optimization")
    
    print("\n--- Key Advantages ---")
    print("• Avoids automatic change address generation issues")
    print("• Provides fine-grained control over transaction inputs")
    print("• Enables UTXO consolidation for better performance")
    print("• Offers detailed balance breakdown (confirmed/unconfirmed/locked)")
    print("• Implements proper fee estimation based on transaction size")
    
    print("\n--- Usage Example (Pseudo-code) ---")
    print("""
    # Initialize advanced wallet manager
    advanced_wallet = AdvancedWalletManager(
        rpc_client=rpc,
        db_manager=db,
        min_tip=Decimal('0.01'),
        max_tip=Decimal('1000'),
        withdrawal_fee=Decimal('0.001'),
        use_raw_transactions=True
    )
    
    # Get detailed balance information
    balance_info = advanced_wallet.get_user_balance_advanced(user)
    print(f"Confirmed: {balance_info['confirmed']} TRMP")
    print(f"Unconfirmed: {balance_info['unconfirmed']} TRMP")
    print(f"UTXO Count: {balance_info['utxo_count']}")
    
    # Perform UTXO analysis
    utxo_analysis = advanced_wallet.get_utxo_analysis(user)
    if utxo_analysis['consolidation_recommended']:
        print("UTXO consolidation recommended!")
        success, msg = advanced_wallet.consolidate_utxos(user)
    
    # Send withdrawal using raw transactions
    success, msg, tx_id = advanced_wallet.withdraw_to_address_raw(
        user, "DTmYzGZtkkTv4kSKCnYbLFSMeYSzKPKHs6", Decimal('1.0')
    )
    """)


def demonstrate_blockchain_queries(rpc: TrumpowRPC):
    """Demonstrate blockchain query capabilities."""
    print("\n" + "="*50)
    print("BLOCKCHAIN QUERY DEMONSTRATION")
    print("="*50)
    
    try:
        # Get best block information
        print("\n--- Current Blockchain State ---")
        best_hash = rpc.get_best_block_hash()
        print(f"Best Block Hash: {best_hash}")
        
        block_count = rpc.get_block_count()
        print(f"Block Count: {block_count}")
        
        # Get information about recent blocks
        print(f"\n--- Recent Block Information ---")
        for i in range(min(3, block_count)):  # Last 3 blocks
            height = block_count - i
            try:
                block_hash = rpc.get_block_hash(height)
                block_info = rpc.get_block(block_hash, 1)  # Verbose format
                
                print(f"Block {height}:")
                print(f"  Hash: {block_hash}")
                print(f"  Time: {datetime.fromtimestamp(block_info.get('time', 0))}")
                print(f"  Transactions: {len(block_info.get('tx', []))}")
                print(f"  Size: {block_info.get('size', 0)} bytes")
                
            except TrumpowRPCError as e:
                print(f"  Error getting block {height}: {e}")
        
        # Get chain tips
        print(f"\n--- Chain Tips ---")
        try:
            chain_tips = rpc.get_chain_tips()
            for tip in chain_tips:
                status = tip.get('status', 'unknown')
                height = tip.get('height', 0)
                hash_val = tip.get('hash', 'unknown')
                branch_len = tip.get('branchlen', 0)
                
                print(f"  {status.title()} chain at height {height}")
                print(f"    Hash: {hash_val}")
                if branch_len > 0:
                    print(f"    Branch length: {branch_len}")
        except TrumpowRPCError as e:
            print(f"Error getting chain tips: {e}")
            
    except TrumpowRPCError as e:
        print(f"Error in blockchain query demonstration: {e}")


def main():
    """Main function to run all demonstrations."""
    setup_logging()
    
    print("Trumpow Advanced RPC Capabilities Demonstration")
    print("=" * 60)
    
    # Configuration - modify these values for your setup
    RPC_HOST = os.getenv('TRMP_RPC_HOST', '127.0.0.1')
    RPC_PORT = int(os.getenv('TRMP_RPC_PORT', '15612'))
    RPC_USER = os.getenv('TRMP_RPC_USER', 'rpcuser')
    RPC_PASSWORD = os.getenv('TRMP_RPC_PASSWORD', 'rpcpassword')
    
    print(f"Connecting to Trumpow node at {RPC_HOST}:{RPC_PORT}")
    
    try:
        # Initialize RPC client
        rpc = TrumpowRPC(
            host=RPC_HOST,
            port=RPC_PORT,
            user=RPC_USER,
            password=RPC_PASSWORD
        )
        
        # Test connection
        if not rpc.test_connection():
            print("❌ Failed to connect to Trumpow node!")
            print("Please check your RPC configuration and ensure the node is running.")
            return False
        
        print("✅ Successfully connected to Trumpow node!")
        
        # Run demonstrations
        demonstrate_basic_rpc_methods(rpc)
        demonstrate_blockchain_queries(rpc)
        demonstrate_utxo_management(rpc)
        demonstrate_raw_transactions(rpc)
        demonstrate_advanced_wallet_manager()
        
        print("\n" + "="*60)
        print("SUMMARY OF ENHANCED CAPABILITIES")
        print("="*60)
        print("✅ Comprehensive RPC method coverage")
        print("✅ Raw transaction building and signing")
        print("✅ UTXO management and analysis")
        print("✅ Advanced wallet management with proper transaction control")
        print("✅ Fee estimation and optimization")
        print("✅ Blockchain query capabilities")
        print("✅ Network and node management")
        print("✅ Fallback mechanisms for reliability")
        
        print("\nThe enhanced RPC client provides all the tools needed for")
        print("proper transaction construction while avoiding change address issues.")
        
        return True
        
    except TrumpowRPCError as e:
        print(f"❌ RPC Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)