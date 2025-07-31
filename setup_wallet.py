#!/usr/bin/env python3
"""
Setup script for Trumpow tip bot wallet.

This script helps set up the Trumpow wallet for use with the tip bot.
"""

import sys
import logging
from config import Config
from trmp_rpc import TrumpowRPC, TrumpowRPCError


def setup_wallet():
    """Setup the Trumpow wallet for the tip bot."""
    print("🚀 Setting up Trumpow Tip Bot Wallet...")
    
    try:
        # Load configuration
        config = Config()
        print(f"✓ Configuration loaded")
        
        # Connect to Trumpow RPC
        rpc = TrumpowRPC(
            host=config.TRMP_RPC_HOST,
            port=config.TRMP_RPC_PORT,
            user=config.TRMP_RPC_USER,
            password=config.TRMP_RPC_PASSWORD,
            wallet=config.TRMP_RPC_WALLET
        )
        
        # Test connection
        if not rpc.test_connection():
            print("❌ Could not connect to Trumpow RPC server")
            print("\nPlease check:")
            print("- Trumpow daemon is running")
            print("- RPC credentials are correct in .env file")
            print("- RPC port is accessible")
            return False
        
        print("✓ Connected to Trumpow RPC server")
        
        # Get network info
        try:
            info = rpc.get_network_info()
            blockchain_info = rpc.get_blockchain_info()
            
            print(f"✓ Network: {info.get('subversion', 'Unknown')}")
            print(f"✓ Connections: {info.get('connections', 0)}")
            print(f"✓ Block height: {blockchain_info.get('blocks', 0)}")
            print(f"✓ Network active: {info.get('networkactive', False)}")
            
        except TrumpowRPCError as e:
            print(f"⚠️  Warning: Could not get network info: {e}")
        
        # Check wallet
        try:
            wallet_info = rpc.get_wallet_info()
            print(f"✓ Wallet version: {wallet_info.get('walletversion', 'Unknown')}")
            
            # Check if wallet is encrypted
            if wallet_info.get('unlocked_until', 0) == 0 and 'encrypted' in str(wallet_info):
                print("⚠️  Wallet appears to be encrypted. Make sure it's unlocked for the bot to function properly.")
            
        except TrumpowRPCError as e:
            print(f"⚠️  Warning: Could not get wallet info: {e}")
        
        # Get initial balance
        try:
            accounts = rpc.list_accounts()
            total_balance = sum(accounts.values())
            print(f"✓ Total wallet balance: {total_balance} TRMP")
            print(f"✓ Number of accounts: {len(accounts)}")
            
        except TrumpowRPCError as e:
            print(f"⚠️  Warning: Could not get balance info: {e}")
        
        # Create a test account to verify functionality
        try:
            test_address = rpc.get_new_address("tipbot_test")
            print(f"✓ Test address created: {test_address}")
            
            # Validate the address
            addr_info = rpc.validate_address(test_address)
            if addr_info.get('isvalid', False):
                print("✓ Address validation successful")
            else:
                print("❌ Address validation failed")
                return False
                
        except TrumpowRPCError as e:
            print(f"❌ Could not create test address: {e}")
            return False
        
        print("\n🎉 Wallet setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Set your Telegram bot token in .env")
        print("3. Run: python tip_bot.py")
        print("\nMake sure your Trumpow daemon stays running while the bot is active.")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)  # Reduce log output during setup
    
    success = setup_wallet()
    sys.exit(0 if success else 1)