# 🚀 TRMP Tip Bot - Quick Start Guide

Get your Trumpow (TRMP) Telegram tip bot running in minutes!

## Prerequisites

1. **Running TRMP Node** with RPC enabled
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **Python 3.8+** installed

## 1. Quick Setup

```bash
# Clone and install
git clone <your-repo>
cd trmp-tipbot
pip install -r requirements.txt

# Auto-setup (creates .env from template)
python setup.py
```

## 2. Configure Your Bot

Edit the `.env` file with your settings:

```bash
# Required settings
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TRMP_RPC_USER=your_rpc_username
TRMP_RPC_PASSWORD=your_rpc_password
ADMIN_USERNAMES=your_telegram_username

# Optional (defaults work for most setups)
TRMP_RPC_HOST=localhost
TRMP_RPC_PORT=22555
```

## 3. TRMP Node Configuration

Add to your `trumpow.conf`:

```conf
rpcuser=your_rpc_username
rpcpassword=your_rpc_password
rpcport=22555
rpcallowip=127.0.0.1
wallet=tipbot
```

## 4. Run the Bot

```bash
# Development mode (local testing)
python tipbot/app.py

# Production mode
DEBUG=False python tipbot/app.py
```

## 🎯 Test Your Bot

1. Message your bot: `/start`
2. Check help: `/help`
3. Check price: `/price`
4. Admin stats: `/stats` (if you're admin)

## 🐳 Docker Quick Start

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run with Docker Compose
docker-compose up -d
```

## 🔧 Common Issues

### Bot Not Responding
- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify bot token has message permissions

### RPC Connection Failed
- Check TRMP node is running
- Verify `TRMP_RPC_USER` and `TRMP_RPC_PASSWORD`
- Ensure `rpcallowip=127.0.0.1` in trumpow.conf

### Database Errors
- For SQLite: Check write permissions in directory
- For PostgreSQL: Verify `DATABASE_URL` format

## 📋 Essential Commands

### User Commands
```
/start - Create wallet
/deposit - Get deposit address (DM only)
/balance - Check balance
/tip 100 @username - Send 100 TRMP
/withdraw 50 <address> - Withdraw (DM only)
/price - Show TRMP price
```

### Admin Commands
```
/stats - Bot statistics
/wallet_info - Wallet details
/recent_transactions - Recent activity
```

## 🛡️ Security Notes

- **Deposit/Withdraw**: Only work in private messages
- **Admin Commands**: Restricted to `ADMIN_USERNAMES`
- **Address Validation**: All addresses validated before sending
- **Amount Limits**: Configurable min/max tip amounts

## 🆘 Need Help?

1. Check logs for error messages
2. Verify all environment variables
3. Test TRMP node RPC connection manually
4. Review the full README.md for detailed setup

---

**Ready to tip? Let's go! 🚀**