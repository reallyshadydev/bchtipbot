# Trumpow Tip Bot - Project Structure

## Core Files

### Main Application
- **`tip_bot.py`** - Main Telegram bot application with command handlers
- **`config.py`** - Configuration manager for loading settings from .env
- **`trmp_rpc.py`** - Trumpow RPC client wrapper for blockchain communication  
- **`wallet_manager.py`** - Wallet and transaction management layer
- **`database.py`** - SQLite database models and operations

### Configuration & Setup
- **`.env.example`** - Template for environment configuration
- **`requirements.txt`** - Python dependencies
- **`setup_wallet.py`** - Wallet setup and diagnostic script
- **`start_bot.sh`** - Startup script with pre-flight checks

### Deployment
- **`systemd/trumpow-tipbot.service`** - Systemd service configuration
- **`README.md`** - Complete setup and usage documentation

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Telegram Bot  │────▶│  Wallet Manager  │────▶│  Trumpow RPC    │
│   (tip_bot.py)  │     │(wallet_manager.py)│     │  (trmp_rpc.py)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Config        │     │   Database       │     │   Trumpow Node  │
│  (config.py)    │     │ (database.py)    │     │  (External)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Key Features Implemented

### ✅ Core Functionality
- **User wallet management** - Automatic address generation per user
- **Tip system** - Send TRMP between Telegram users
- **Withdrawal system** - Send TRMP to external addresses
- **Transaction history** - View recent transactions
- **Balance checking** - Real-time balance updates

### ✅ Security Features
- **Rate limiting** - Configurable limits on tips and withdrawals
- **Input validation** - Amount and address validation
- **Private message enforcement** - Sensitive operations require private chats
- **Transaction logging** - All operations logged to database

### ✅ Admin Features
- **Statistics dashboard** - Bot usage and network stats
- **User management** - Admin-only commands
- **Configuration management** - Environment-based configuration

### ✅ Reliability Features
- **Error handling** - Comprehensive error handling and logging
- **Connection testing** - RPC connection validation
- **Graceful degradation** - Continues operation during temporary issues
- **Service management** - Systemd integration for production deployment

## Database Schema

### Users Table
```sql
- user_id (INTEGER PRIMARY KEY) - Telegram user ID
- username (TEXT) - Telegram username
- trmp_account (TEXT) - Internal account name
- trmp_address (TEXT) - Deposit address
- created_at (TIMESTAMP) - Account creation time
- is_active (BOOLEAN) - Account status
- daily_tip_count (INTEGER) - Rate limiting counter
- daily_withdrawal_amount (DECIMAL) - Daily withdrawal tracking
```

### Transactions Table
```sql
- id (INTEGER PRIMARY KEY) - Transaction ID
- from_user_id/to_user_id (INTEGER) - Participants
- amount (DECIMAL) - Transaction amount
- fee (DECIMAL) - Transaction fee
- tx_type (TEXT) - 'tip', 'withdraw', 'deposit'
- status (TEXT) - 'pending', 'confirmed', 'failed'
- txid (TEXT) - Blockchain transaction ID
- created_at/confirmed_at (TIMESTAMP) - Timing
```

### Rate Limits Table
```sql
- user_id (INTEGER PRIMARY KEY) - User reference
- tips_today (INTEGER) - Daily tip counter
- withdrawals_today (INTEGER) - Daily withdrawal counter
- last_reset_date (DATE) - Reset tracking
```

## Configuration Options

All settings are managed through `.env` file:

### Required Settings
- `TELEGRAM_BOT_TOKEN` - Telegram bot API token
- `TRMP_RPC_USER/PASSWORD` - Trumpow node credentials
- `TRMP_RPC_HOST/PORT` - Trumpow node connection

### Optional Settings  
- `MINIMUM_TIP/MAXIMUM_TIP` - Amount limits
- `WITHDRAWAL_FEE` - Fee for withdrawals
- `RATE_LIMIT_*` - Rate limiting configuration
- `ADMIN_USERNAMES` - Administrator accounts
- `LOG_LEVEL/LOG_FILE` - Logging configuration

## Supported Commands

### User Commands
- `/start` - Initialize wallet
- `/balance` - Check balance
- `/tip <amount> @user` - Send tips
- `/withdraw <amount> <address>` - Withdraw funds
- `/deposit` - Get deposit address
- `/history` - Transaction history
- `/help` - Command reference

### Admin Commands
- `/stats` - Bot statistics and network info

## Error Handling

The bot implements comprehensive error handling:

1. **RPC Errors** - Network and node communication issues
2. **Database Errors** - SQLite operation failures  
3. **Validation Errors** - Invalid amounts, addresses, etc.
4. **Rate Limit Errors** - Exceeded usage limits
5. **Permission Errors** - Unauthorized operations
6. **Network Errors** - Telegram API issues

All errors are logged with appropriate detail for debugging while providing user-friendly messages to Telegram users.

## Production Deployment

The bot is designed for production deployment with:

- **Systemd service** for automatic startup/restart
- **Comprehensive logging** for monitoring and debugging
- **Configuration validation** at startup
- **Connection testing** before accepting commands
- **Security hardening** through systemd service restrictions
- **Resource management** with proper cleanup and connection pooling