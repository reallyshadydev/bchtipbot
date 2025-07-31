#!/usr/bin/env python3
"""
Setup script for Dogecoin Telegram Tip Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print("✅ Python version check passed")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_local_file = Path(".env.local")
    
    if not env_local_file.exists():
        if env_file.exists():
            # Copy .env to .env.local
            with open(env_file, 'r') as src, open(env_local_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env.local from template")
        else:
            print("❌ .env template file not found")
            return False
    else:
        print("✅ .env.local already exists")
    
    return True

def check_dogecoin_core():
    """Check if Dogecoin Core is accessible"""
    print("🐕 Checking Dogecoin Core connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv(".env.local")
        
        from tipbot.dogecoin_client import get_dogecoin_client
        
        client = get_dogecoin_client()
        network_info = client.get_network_info()
        
        if network_info:
            print(f"✅ Connected to Dogecoin Core (version: {network_info.get('version', 'unknown')})")
            return True
        else:
            print("❌ Failed to connect to Dogecoin Core")
            return False
            
    except Exception as e:
        print(f"❌ Dogecoin Core connection failed: {e}")
        print("\n🔧 Make sure:")
        print("   1. Dogecoin Core is running")
        print("   2. RPC is enabled in dogecoin.conf")
        print("   3. RPC credentials in .env.local are correct")
        return False

def validate_env_config():
    """Validate environment configuration"""
    print("⚙️ Validating configuration...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DOGECOIN_RPC_USER", 
        "DOGECOIN_RPC_PASSWORD",
        "FEE_ADDRESS"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please edit .env.local and add the missing variables")
        return False
    
    print("✅ Configuration validation passed")
    return True

def run_tests():
    """Run basic tests"""
    print("🧪 Running tests...")
    try:
        subprocess.check_call([sys.executable, "run_tests.py"])
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Some tests failed")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Dogecoin Telegram Tip Bot\n")
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create env file
    if not create_env_file():
        print("\n❌ Setup failed: Could not create environment file")
        return
    
    print("\n📝 Please edit .env.local with your configuration:")
    print("   - TELEGRAM_BOT_TOKEN: Your Telegram bot token")
    print("   - DOGECOIN_RPC_USER: Your Dogecoin Core RPC username")
    print("   - DOGECOIN_RPC_PASSWORD: Your Dogecoin Core RPC password")
    print("   - FEE_ADDRESS: Your Dogecoin address for collecting fees")
    print("   - ADMIN_LIST: Your Telegram username")
    
    input("\nPress Enter after you've configured .env.local...")
    
    # Load the updated environment
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    # Validate configuration
    if not validate_env_config():
        print("\n❌ Setup failed: Invalid configuration")
        return
    
    # Check Dogecoin Core connection
    if not check_dogecoin_core():
        print("\n❌ Setup failed: Cannot connect to Dogecoin Core")
        return
    
    # Run tests
    if not run_tests():
        print("\n⚠️  Setup completed with test failures")
    else:
        print("\n✅ Setup completed successfully!")
    
    print("\n🎉 Your Dogecoin Tip Bot is ready!")
    print("   Run: python3 tipbot/app.py")

if __name__ == "__main__":
    main()