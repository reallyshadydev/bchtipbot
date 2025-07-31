#!/usr/bin/env python3
"""
Setup script for TRMP Tip Bot
"""

import os
import sys

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        print("Creating .env file from .env.example...")
        import shutil
        shutil.copy('.env.example', '.env')
        print("✅ .env file created. Please edit it with your configuration.")
        return True
    return False

def check_requirements():
    """Check if requirements are installed"""
    try:
        import telegram
        import bitcoinrpc
        import peewee
        import requests
        import dotenv
        print("✅ All required packages are installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def validate_config():
    """Validate basic configuration"""
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it from .env.example")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TRMP_RPC_USER', 
        'TRMP_RPC_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please edit your .env file and add these variables.")
        return False
    
    print("✅ Configuration validated.")
    return True

def main():
    """Main setup function"""
    print("🚀 TRMP Tip Bot Setup")
    print("=" * 50)
    
    # Create .env file
    env_created = create_env_file()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # If .env was just created, remind user to configure it
    if env_created:
        print("\n⚠️  Please edit the .env file with your configuration before running the bot.")
        print("Required settings:")
        print("- TELEGRAM_BOT_TOKEN (from @BotFather)")
        print("- TRMP_RPC_USER and TRMP_RPC_PASSWORD (from your TRMP node)")
        print("- ADMIN_USERNAMES (your Telegram username)")
        sys.exit(0)
    
    # Validate configuration
    if not validate_config():
        sys.exit(1)
    
    print("\n✅ Setup complete! You can now run the bot:")
    print("   python tipbot/app.py")
    print("\nFor development with auto-reload:")
    print("   DEBUG=True python tipbot/app.py")

if __name__ == "__main__":
    main()