<div align="center">
  <img src="tippie.png" width="100">
</div>

<div align="center">
  <h3>Trumpow (TRMP) Telegram Tip Bot</h3>
</div>

<div align="center">
  <img src="https://github.com/merc1er/bchtipbot/workflows/Run%20tests/badge.svg" alt="tests">
  <a href="https://www.codefactor.io/repository/github/merc1er/bchtipbot"><img src="https://www.codefactor.io/repository/github/merc1er/bchtipbot/badge" alt="CodeFactor"></a>
  <a href="https://codecov.io/gh/merc1er/bchtipbot"><img src="https://codecov.io/gh/merc1er/bchtipbot/branch/master/graph/badge.svg?token=CIQBH8S6HA"></a>
</div>

---

## 🚀 About

A Telegram tip bot for **Trumpow (TRMP)**, a cryptocurrency project that is a fork of Dogecoin Core. Since Trumpow uses the same RPC interface and commands as Dogecoin, this bot leverages existing Dogecoin-compatible tools and libraries.

### ✨ Features

- 💰 **Wallet Management**: Automatic wallet creation, deposit addresses, balance checking
- 🎯 **Tipping System**: Send TRMP to other users instantly
- 💸 **Withdrawals**: Secure withdrawal to external TRMP addresses  
- 📊 **Price Integration**: Real-time TRMP price in multiple currencies
- 🔧 **Admin Tools**: Comprehensive admin panel for bot management
- ⚙️ **Configurable**: Environment-based configuration with `.env` support
- 🔒 **Secure**: Private message requirements for sensitive operations

---

## 📱 Usage

### User Commands

#### 💰 Wallet Commands
```
/start - Create your TRMP wallet
/deposit - Get your deposit address (private message only)
/balance - Check your balance
/balance [currency] - Check balance in USD, EUR, BTC, ETH
/withdraw <amount> <address> - Withdraw TRMP (private message only)
/withdraw all <address> - Withdraw all TRMP minus fees
```

#### 🎯 Tipping Commands
```
/tip <amount> @username - Send TRMP to another user
/tip <amount> satoshi @username - Tip in satoshi (1 TRMP = 100,000,000 satoshi)
```

#### 📊 Price Commands
```
/price - Show current TRMP price in USD
/price [currency] - Show price in EUR, BTC, ETH
```

#### ℹ️ Info Commands
```
/help - Show help message with all commands
```

### Examples

```bash
# Basic tip
/tip 100 @alice

# Tip in satoshi
/tip 5000000 satoshi @bob

# Check balance in different currencies
/balance usd
/balance btc

# Withdraw specific amount
/withdraw 50 TRMPAddressHere

# Withdraw everything
/withdraw all TRMPAddressHere
```

---

## 🛠️ Setup & Installation

### Prerequisites

1. **Trumpow Core Node**: Running TRMP node with RPC enabled
2. **Telegram Bot Token**: From [@BotFather](https://t.me/BotFather)
3. **Python 3.8+**: For running the bot
4. **Database**: SQLite (development) or PostgreSQL (production)

### 1. Clone & Install

```bash
git clone <your-repo>
cd trmp-tipbot
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Trumpow (TRMP) RPC Configuration
TRMP_RPC_HOST=localhost
TRMP_RPC_PORT=22555
TRMP_RPC_USER=your_rpc_username
TRMP_RPC_PASSWORD=your_rpc_password
TRMP_RPC_WALLET=tipbot

# Database Configuration
DATABASE_URL=sqlite:///trmp_tipbot.db

# Bot Settings
DEBUG=True
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PORT=8443

# Fee Configuration
FEE_ADDRESS=your_trmp_fee_address_here
FEE_PERCENTAGE=0.01
MINIMUM_TIP=1.0
MAXIMUM_TIP=10000.0

# Admin Configuration
ADMIN_USERNAMES=your_telegram_username

# Logging
LOG_LEVEL=INFO
```

### 3. Trumpow Core Configuration

Add to your `trumpow.conf`:

```conf
# RPC Settings
rpcuser=your_rpc_username
rpcpassword=your_rpc_password
rpcport=22555
rpcallowip=127.0.0.1

# Wallet Settings
wallet=tipbot
```

### 4. Run the Bot

Development mode:
```bash
python tipbot/app.py
```

Production mode (set `DEBUG=False` in `.env`):
```bash
python tipbot/app.py
```

---

## 👨‍💼 Admin Commands

Admins (configured in `ADMIN_USERNAMES`) have access to additional commands:

```bash
/stats - Show bot statistics
/wallet_info - Show detailed wallet information
/backup_users - Create user data backup
/broadcast <message> - Send message to all users
/recent_transactions [limit] - Show recent transactions
```

---

## 🏗️ Architecture

### Core Components

- **`trmp_wallet.py`**: TRMP wallet interface using Dogecoin RPC
- **`commands.py`**: User command handlers
- **`admin/commands.py`**: Admin command handlers
- **`rates.py`**: Price fetching and conversion
- **`db/models.py`**: Database models (User, Transaction)
- **`settings.py`**: Configuration management

### Database Schema

**Users Table:**
- `username` - Telegram username
- `trmp_address` - TRMP deposit address
- `created_at` - Account creation timestamp
- `is_active` - Account status

**Transactions Table:**
- `from_user` / `to_user` - Transaction participants
- `amount` - Transaction amount in TRMP
- `fee` - Transaction fee
- `txid` - Blockchain transaction ID
- `tx_type` - Type: 'tip', 'withdraw', 'deposit'
- `status` - Status: 'pending', 'confirmed', 'failed'

---

## 🚀 Deployment

### Heroku Deployment

1. Create Heroku app:
```bash
heroku create your-trmp-tipbot
```

2. Set environment variables:
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set TRMP_RPC_HOST=your_host
# ... set all required env vars
```

3. Deploy:
```bash
git push heroku main
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "tipbot/app.py"]
```

---

## 🔒 Security Considerations

1. **Private Operations**: Sensitive commands (deposit, withdraw) require private messages
2. **Address Validation**: All TRMP addresses are validated before transactions
3. **Amount Limits**: Configurable minimum/maximum tip amounts
4. **Rate Limiting**: Framework for implementing rate limits (TODO)
5. **Input Sanitization**: User inputs are sanitized to prevent injection attacks

---

## 🧪 Testing

Run tests:
```bash
python run_tests.py
```

With coverage:
```bash
pip install coverage
coverage run -m unittest
coverage html
```

Code formatting:
```bash
black .
```

---

## 📋 Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456:ABC-DEF...` |
| `TRMP_RPC_USER` | RPC username | `rpcuser` |
| `TRMP_RPC_PASSWORD` | RPC password | `rpcpass123` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRMP_RPC_HOST` | `localhost` | TRMP node host |
| `TRMP_RPC_PORT` | `22555` | TRMP RPC port |
| `TRMP_RPC_WALLET` | `tipbot` | Wallet name |
| `DATABASE_URL` | `sqlite:///trmp_tipbot.db` | Database connection |
| `DEBUG` | `False` | Debug mode |
| `FEE_PERCENTAGE` | `0.01` | Fee percentage (1%) |
| `MINIMUM_TIP` | `1.0` | Minimum tip amount |
| `MAXIMUM_TIP` | `10000.0` | Maximum tip amount |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code formatting: `black .`
6. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🆘 Support

- Create an issue for bugs or feature requests
- Join our community for support and discussions
- Check the logs for troubleshooting information

---

## 🎯 Roadmap

- [ ] Enhanced price API integration
- [ ] Rate limiting implementation  
- [ ] Multi-language support
- [ ] Advanced admin dashboard
- [ ] Transaction history export
- [ ] Sticker support for fun interactions
- [ ] Group chat tip notifications
- [ ] Mobile-friendly web interface

---

**Built with ❤️ for the Trumpow community**
