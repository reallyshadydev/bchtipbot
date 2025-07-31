# Trumpow Telegram Tip Bot

A Telegram bot that allows users to send and receive TRMP (Trumpow) cryptocurrency directly through Telegram messages.

## Features

- **Tip TRMP**: Send TRMP to other users via Telegram
- **Wallet Management**: Automatic wallet creation for each user
- **Balance Checking**: Check your TRMP balance
- **Transaction History**: View recent transactions
- **Deposit/Withdraw**: Deposit TRMP to your bot wallet or withdraw to external addresses
- **Security**: Rate limiting and transaction validation
- **Configurable**: Easy configuration via .env file

## Prerequisites

1. **Trumpow Node**: You need a running Trumpow node with RPC enabled
2. **Telegram Bot Token**: Create a bot via @BotFather on Telegram
3. **Python 3.8+**: Required for the bot to run

## Installation

### Step 1: Clone and Setup
```bash
git clone <repository-url>
cd trumpow-tip-bot
pip3 install -r requirements.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

**Required configuration:**
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather on Telegram
- `TRMP_RPC_USER` - Your Trumpow RPC username
- `TRMP_RPC_PASSWORD` - Your Trumpow RPC password
- `TRMP_RPC_HOST` - Trumpow daemon host (default: localhost)
- `TRMP_RPC_PORT` - Trumpow daemon RPC port (default: 22555)

### Step 3: Setup Wallet
```bash
python3 setup_wallet.py
```
This script will test your Trumpow RPC connection and verify wallet functionality.

### Step 4: Start Bot
```bash
# Option 1: Use startup script (recommended)
./start_bot.sh

# Option 2: Run directly
python3 tip_bot.py
```

### Step 5: Test Bot
1. Start a chat with your bot on Telegram
2. Send `/start` to create your wallet
3. Try `/help` to see all commands

## Configuration

All configuration is done via the `.env` file. See `.env.example` for all available options.

## Bot Commands

- `/start` - Initialize your wallet
- `/balance` - Check your TRMP balance
- `/tip <amount> <user>` - Tip TRMP to another user
- `/deposit` - Get your deposit address
- `/withdraw <amount> <address>` - Withdraw TRMP to external address
- `/history` - View recent transactions
- `/help` - Show help message

## Security Notes

- The bot uses separate accounts for each user
- Private keys are managed securely by the Trumpow node
- Rate limiting prevents spam and abuse
- All transactions are logged

## Deployment Options

### Option 1: Run as Systemd Service (Linux)
```bash
# Copy service file
sudo cp systemd/trumpow-tipbot.service /etc/systemd/system/

# Edit paths in service file as needed
sudo nano /etc/systemd/system/trumpow-tipbot.service

# Enable and start service
sudo systemctl enable trumpow-tipbot
sudo systemctl start trumpow-tipbot

# Check status
sudo systemctl status trumpow-tipbot
```

### Option 2: Run with Screen/Tmux
```bash
# Using screen
screen -S tipbot ./start_bot.sh

# Using tmux
tmux new-session -d -s tipbot './start_bot.sh'
```

## Trumpow Node Configuration

Add these settings to your `trumpow.conf`:

```conf
# RPC Settings
rpcuser=your_rpc_username
rpcpassword=your_rpc_password
rpcport=22555
rpcallowip=127.0.0.1

# Wallet Settings
wallet=tipbot

# Network Settings (optional)
server=1
daemon=1
```

## Troubleshooting

### Common Issues

1. **"Could not connect to Trumpow RPC server"**
   - Ensure Trumpow daemon is running
   - Check RPC credentials in `.env`
   - Verify RPC port is accessible

2. **"Permission denied" errors**
   - Make scripts executable: `chmod +x *.py start_bot.sh`
   - Check file permissions and ownership

3. **"Module not found" errors**
   - Install dependencies: `pip3 install -r requirements.txt`
   - Use Python 3.8+ (recommended)

4. **Telegram bot not responding**
   - Verify bot token is correct
   - Check internet connectivity
   - Look at logs for error messages

### Getting Help

Run the setup script for diagnostics:
```bash
python3 setup_wallet.py
```

Check logs:
```bash
tail -f tip_bot.log
```

## Support

For issues or questions, please open an issue in this repository.
