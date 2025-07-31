# 🚀 Quick Start Guide - Dogecoin Telegram Tip Bot

This guide will help you set up your Dogecoin Telegram tip bot in just a few minutes.

## 📋 Prerequisites

1. **Dogecoin Core** - Download and install from [dogecoin.com](https://dogecoin.com/)
2. **Python 3.7+** - Check with `python3 --version`
3. **Telegram Bot Token** - Get one from [@BotFather](https://t.me/BotFather)

## ⚡ Quick Setup

### Step 1: Configure Dogecoin Core

1. **Locate your Dogecoin data directory:**
   - Linux: `~/.dogecoin/`
   - macOS: `~/Library/Application Support/Dogecoin/`
   - Windows: `%APPDATA%\Dogecoin\`

2. **Create or edit `dogecoin.conf`:**
   ```bash
   cp dogecoin.conf.example ~/.dogecoin/dogecoin.conf
   ```

3. **Edit the configuration:**
   ```conf
   server=1
   rpcuser=myuser
   rpcpassword=mypassword123
   rpcallowip=127.0.0.1
   rpcport=22555
   ```

4. **Start Dogecoin Core** and let it sync (this may take a while for the first time)

### Step 2: Create Your Telegram Bot

1. **Message [@BotFather](https://t.me/BotFather)** on Telegram
2. **Send `/newbot`** and follow the instructions
3. **Choose a name** (e.g., "My Doge Tip Bot")
4. **Choose a username** (e.g., "mydogetipbot")
5. **Save the bot token** - you'll need it in the next step

### Step 3: Configure the Bot

1. **Run the setup script:**
   ```bash
   python3 setup.py
   ```

2. **Edit `.env.local` when prompted:**
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   DOGECOIN_RPC_USER=myuser
   DOGECOIN_RPC_PASSWORD=mypassword123
   FEE_ADDRESS=DQA6...your_dogecoin_address_here
   ADMIN_LIST=your_telegram_username
   ```

3. **Press Enter** to continue the setup

### Step 4: Run the Bot

```bash
python3 tipbot/app.py
```

## 🎉 You're Done!

Your bot is now running! Test it by:

1. **Starting a chat** with your bot on Telegram
2. **Sending `/start`** to initialize
3. **Sending `/help`** to see available commands
4. **Sending `/deposit`** to get your deposit address
5. **Send some DOGE** to your deposit address
6. **Check balance** with `/balance`

## 🔧 Common Commands

- `/start` - Initialize the bot
- `/deposit` - Get your deposit address
- `/balance` - Check your balance
- `/tip 10 @username` - Tip 10 DOGE to a user
- `/withdraw 5 DQA6...address` - Withdraw 5 DOGE
- `/price` - Check current DOGE price

## 🆘 Troubleshooting

### "Cannot connect to Dogecoin Core"
- Make sure Dogecoin Core is running
- Check your RPC credentials in `.env.local`
- Verify `dogecoin.conf` settings

### "Invalid Telegram bot token"
- Double-check your bot token from @BotFather
- Make sure there are no extra spaces in `.env.local`

### "Address validation failed"
- Ensure Dogecoin Core is fully synced
- Check that your wallet is loaded

### Bot doesn't respond
- Check that your bot is running (`python3 tipbot/app.py`)
- Verify your bot token is correct
- Make sure you've sent `/start` to the bot first

## 🔒 Security Tips

1. **Use strong RPC passwords**
2. **Keep your `.env.local` file secure**
3. **Regular wallet backups**
4. **Monitor bot transactions**
5. **Use a dedicated wallet for the bot**

## 📚 Next Steps

- Read the full [README.md](README.md) for advanced configuration
- Set up monitoring and logging
- Configure production deployment
- Set up automated backups

---

**Need help?** Check the [issues](https://github.com/your-repo/issues) or create a new one!