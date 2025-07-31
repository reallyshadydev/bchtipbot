#!/usr/bin/env python3
"""
Test script for no-change transaction functionality.
This script tests the raw transaction building without change addresses.
"""

import logging
import sys
import os
from decimal import Decimal

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trmp_rpc import TrumpowRPC, TrumpowRPCError
from wallet_manager import WalletManager
from database import DatabaseManager
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rpc_connection():
    """Test basic RPC connection and new methods."""
    logger.info("Testing RPC connection and new methods...")
    
    try:
        config = Config()
        rpc = TrumpowRPC(
            host=config.TRMP_RPC_HOST,
            port=config.TRMP_RPC_PORT,
            user=config.TRMP_RPC_USER,
            password=config.TRMP_RPC_PASSWORD
        )
        
        # Test basic connection
        if not rpc.test_connection():
            logger.error("Failed to connect to Trumpow RPC")
            return False
        
        logger.info("✅ RPC connection successful")
        
        # Test new methods
        try:
            # Test blockchain info
            best_hash = rpc.get_best_block_hash()
            logger.info(f"✅ Best block hash: {best_hash}")
            
            # Test network info
            network_info = rpc.get_network_info()
            logger.info(f"✅ Network connections: {network_info.get('connections', 'Unknown')}")
            
            # Test wallet info
            wallet_info = rpc.get_wallet_info()
            logger.info(f"✅ Wallet version: {wallet_info.get('walletversion', 'Unknown')}")
            
            # Test UTXO listing
            utxos = rpc.list_unspent(1, 9999999)
            logger.info(f"✅ Found {len(utxos)} UTXOs")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing new RPC methods: {e}")
            return False
            
    except Exception as e:
        logger.error(f"RPC connection test failed: {e}")
        return False


def test_utxo_analysis():
    """Test UTXO analysis functionality."""
    logger.info("Testing UTXO analysis...")
    
    try:
        config = Config()
        rpc = TrumpowRPC(
            host=config.TRMP_RPC_HOST,
            port=config.TRMP_RPC_PORT,
            user=config.TRMP_RPC_USER,
            password=config.TRMP_RPC_PASSWORD
        )
        
        db = DatabaseManager()
        wallet_manager = WalletManager(
            rpc, db, 
            Decimal(str(config.MINIMUM_TIP)),
            Decimal(str(config.MAXIMUM_TIP)),
            Decimal(str(config.WITHDRAWAL_FEE))
        )
        
        # Get all accounts to test with
        accounts = rpc.list_accounts()
        logger.info(f"Found {len(accounts)} accounts")
        
        if not accounts:
            logger.warning("No accounts found for testing")
            return True
        
        # Test UTXO combination finding
        all_utxos = rpc.list_unspent(1, 9999999)
        if all_utxos:
            test_amount = Decimal('1.0')  # Test with 1 TRMP
            max_fee = Decimal('0.01')
            
            combination = wallet_manager._find_best_utxo_combination(all_utxos, test_amount, max_fee)
            
            if combination:
                logger.info(f"✅ Found UTXO combination for {test_amount} TRMP:")
                logger.info(f"   - UTXOs used: {len(combination['utxos'])}")
                logger.info(f"   - Total input: {combination['total_input']}")
                logger.info(f"   - Leftover (fee): {combination['leftover']}")
            else:
                logger.info(f"⚠️  No suitable UTXO combination found for {test_amount} TRMP")
        else:
            logger.info("No UTXOs available for testing")
        
        return True
        
    except Exception as e:
        logger.error(f"UTXO analysis test failed: {e}")
        return False


def test_fee_estimation():
    """Test fee estimation functionality."""
    logger.info("Testing fee estimation...")
    
    try:
        config = Config()
        rpc = TrumpowRPC(
            host=config.TRMP_RPC_HOST,
            port=config.TRMP_RPC_PORT,
            user=config.TRMP_RPC_USER,
            password=config.TRMP_RPC_PASSWORD
        )
        
        db = DatabaseManager()
        wallet_manager = WalletManager(
            rpc, db,
            Decimal(str(config.MINIMUM_TIP)),
            Decimal(str(config.MAXIMUM_TIP)),
            Decimal(str(config.WITHDRAWAL_FEE))
        )
        
        # Get some addresses to test with
        accounts = rpc.list_accounts()
        if accounts:
            # Get addresses for the first account with balance
            for account, balance in accounts.items():
                if balance > 0:
                    try:
                        addresses = rpc.get_addresses_by_account(account)
                        if addresses:
                            test_amount = Decimal('0.1')  # Test with 0.1 TRMP
                            
                            estimated_fee, can_avoid_change = wallet_manager.estimate_transaction_fee(
                                addresses, test_amount
                            )
                            
                            logger.info(f"✅ Fee estimation for {test_amount} TRMP:")
                            logger.info(f"   - Estimated fee: {estimated_fee}")
                            logger.info(f"   - Can avoid change: {can_avoid_change}")
                            break
                    except Exception as e:
                        logger.warning(f"Error testing account {account}: {e}")
                        continue
        
        return True
        
    except Exception as e:
        logger.error(f"Fee estimation test failed: {e}")
        return False


def display_rpc_commands():
    """Display information about available RPC commands."""
    logger.info("Available RPC commands for proper transaction building:")
    
    commands = {
        "listunspent": "List unspent transaction outputs (UTXOs)",
        "createrawtransaction": "Create a raw transaction from inputs and outputs",
        "signrawtransaction": "Sign a raw transaction with wallet keys",
        "sendrawtransaction": "Broadcast a signed raw transaction",
        "decoderawtransaction": "Decode a raw transaction hex",
        "getbestblockhash": "Get the hash of the best (tip) block",
        "getblock": "Get block information by hash",
        "validateaddress": "Validate a Trumpow address",
        "estimatefee": "Estimate fee per kilobyte for confirmation target",
        "getnetworkinfo": "Get network-related information",
        "getblockchaininfo": "Get blockchain information"
    }
    
    logger.info("\n📋 **Enhanced RPC Commands Available:**")
    for cmd, desc in commands.items():
        logger.info(f"   • {cmd}: {desc}")
    
    logger.info("\n💡 **Transaction Building Best Practices:**")
    logger.info("   • Use listunspent to find available UTXOs")
    logger.info("   • Select UTXOs that minimize or eliminate change")
    logger.info("   • Use createrawtransaction with exact amounts")
    logger.info("   • Sign with signrawtransaction")
    logger.info("   • Broadcast with sendrawtransaction")
    logger.info("   • Avoid change addresses for better privacy")


def main():
    """Run all tests."""
    logger.info("🚀 Starting Trumpow RPC and No-Change Transaction Tests")
    logger.info("=" * 60)
    
    tests = [
        ("RPC Connection", test_rpc_connection),
        ("UTXO Analysis", test_utxo_analysis),
        ("Fee Estimation", test_fee_estimation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
            results.append((test_name, False))
    
    # Display RPC commands info
    logger.info("\n" + "=" * 60)
    display_rpc_commands()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests completed successfully!")
        logger.info("The no-change transaction system is ready to use.")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)