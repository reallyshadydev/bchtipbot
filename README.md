<div align="center">
  <img src="tippie.png" width="100">
</div>

<div align="center">
  <h3>Dogecoin Telegram Tipping Bot</h3>
</div>

<div align="center">
  <img src="https://github.com/merc1er/bchtipbot/workflows/Run%20tests/badge.svg" alt="tests">
  <a href="https://www.codefactor.io/repository/github/merc1er/bchtipbot"><img src="https://www.codefactor.io/repository/github/merc1er/bchtipbot/badge" alt="CodeFactor"></a>
  <a href="https://codecov.io/gh/merc1er/bchtipbot"><img src="https://codecov.io/gh/merc1er/bchtipbot/branch/master/graph/badge.svg?token=CIQBH8S6HA"></a>
</div>

---

## 🐕 Dogecoin Telegram Tip Bot

A Telegram bot that allows users to send Dogecoin tips to each other directly in Telegram chats. The bot integrates with Dogecoin Core via RPC for secure transaction handling.

### 📱 Usage

**Simply create your bot on Telegram and configure it with your Dogecoin Core node.**

#### List of commands

##### Tipping

```
/start - Starts the bot
/deposit - Displays your Dogecoin address for top up
/balance - Shows your balance in Dogecoin
/withdraw - Withdraw your funds. Usage: /withdraw amount|all address
/help - Lists all commands
/tip - Sends a tip. Usage: /tip amount [@username]
```

##### Price

```
/price - Displays the current price of Dogecoin. Usage: /price [currency_code]
```

For example: `/price` (defaults to USD), `/price eur`, `/price btc` and so on.

### ⚙️ Setup and Installation

#### Prerequisites

1. **Dogecoin Core**: You need a running Dogecoin Core node with RPC enabled
2. **Python 3.7+**: Required for the bot
3. **Telegram Bot Token**: Create a bot via @BotFather on Telegram

#### Dogecoin Core Configuration

Add the following to your `dogecoin.conf` file:

```conf
server=1
rpcuser=your_rpc_username
rpcpassword=your_secure_rpc_password
rpcallowip=127.0.0.1
rpcport=22555
```

#### Environment Configuration

1. Copy the `.env` file and fill in your configuration:

```bash
cp .env .env.local
```

2. Edit `.env.local` with your settings:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Dogecoin Core RPC Configuration
DOGECOIN_RPC_HOST=127.0.0.1
DOGECOIN_RPC_PORT=22555
DOGECOIN_RPC_USER=your_rpc_username
DOGECOIN_RPC_PASSWORD=your_rpc_password

# Bot Configuration
DEBUG=True
FEE_ADDRESS=your_dogecoin_fee_address_here
FEE_PERCENTAGE=0.01

# Admin Configuration
ADMIN_LIST=your_telegram_username
```

#### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the bot:

```bash
python3 tipbot/app.py
```

### 🔧 Development

#### Run development server

```shell
pip install -r requirements-dev.txt
python3 tipbot/app.py
```

#### Run tests

```shell
python run_tests.py
```

Or with coverage:

```shell
pip install coverage
coverage run -m unittest
coverage html
```

#### Linting

This project uses [`black`](https://github.com/psf/black) Python code formatter:

```shell
black .
```

### 🚀 Deployment

#### Environment Variables

Set the following environment variables for production:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DOGECOIN_RPC_HOST=127.0.0.1
DOGECOIN_RPC_PORT=22555
DOGECOIN_RPC_USER=your_rpc_username
DOGECOIN_RPC_PASSWORD=your_rpc_password
FEE_ADDRESS=your_dogecoin_fee_address
FEE_PERCENTAGE=0.01
ADMIN_LIST=your_telegram_username
DATABASE_URL=postgresql://user:password@localhost/dbname  # For production
DEBUG=False
```

#### Heroku Deployment

1. Create a Heroku app
2. Set the environment variables in Heroku dashboard
3. Deploy the code

#### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "tipbot/app.py"]
```

### 🔒 Security Notes

- **Never share your RPC credentials**: Keep your Dogecoin Core RPC username and password secure
- **Use a dedicated wallet**: Consider using a separate Dogecoin Core wallet for the bot
- **Regular backups**: Backup your wallet.dat file regularly
- **Monitor transactions**: Keep track of bot transactions for security

### 🛠️ Features

- **Secure**: Uses Dogecoin Core RPC for all transactions
- **Multi-currency**: View balances in various currencies (USD, EUR, BTC, etc.)
- **Fee system**: Configurable fee system for tips
- **Admin commands**: Admin-only commands for bot management
- **Database**: Persistent user data with PostgreSQL/SQLite support

### 📊 Database Schema

The bot uses a simple database schema:

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(30) UNIQUE,
    doge_address VARCHAR(54) UNIQUE,
    created_at DATETIME
);
```

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### 📄 License

This project is open source. Please check the license file for more details.

---

### 🚨 Disclaimer

This bot handles real Dogecoin transactions. Use at your own risk. Always test thoroughly in a development environment before deploying to production. The developers are not responsible for any loss of funds.
