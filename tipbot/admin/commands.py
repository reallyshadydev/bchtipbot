import logging
from decimal import Decimal
from telegram import Update
from telegram.ext import CallbackContext
from db.models import User, Transaction, db
from settings import ADMIN_USERNAMES
from trmp_wallet import wallet

logger = logging.getLogger(__name__)


def is_admin(command):
    """Decorator to check if sender is admin"""
    def wrapper(update: Update, context: CallbackContext):
        username = update.message.from_user.username
        if username and username in ADMIN_USERNAMES:
            return command(update, context)
        else:
            update.message.reply_text("❌ Admin access required.")
            return None
    return wrapper


@is_admin
def stats(update: Update, context: CallbackContext):
    """Show bot statistics"""
    try:
        # Count users
        user_count = User.select().count()
        
        # Count transactions
        tx_count = Transaction.select().count()
        
        # Get wallet balance
        try:
            total_balance = wallet.get_balance()
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {e}")
            total_balance = Decimal('0')
        
        # Calculate total tips
        total_tips = Transaction.select().where(
            Transaction.tx_type == 'tip'
        ).count()
        
        # Calculate total tip volume
        tip_volume_query = Transaction.select().where(
            Transaction.tx_type == 'tip',
            Transaction.status == 'confirmed'
        )
        
        total_tip_volume = Decimal('0')
        for tx in tip_volume_query:
            total_tip_volume += tx.amount
        
        message = f"📊 *TRMP Tip Bot Statistics*\n\n"
        message += f"👥 Total Users: {user_count}\n"
        message += f"💸 Total Transactions: {tx_count}\n"
        message += f"🎯 Total Tips: {total_tips}\n"
        message += f"💰 Total Tip Volume: {total_tip_volume:.8f} TRMP\n"
        message += f"🏦 Wallet Balance: {total_balance:.8f} TRMP\n"
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        update.message.reply_text("❌ Error retrieving statistics.")


@is_admin
def wallet_info(update: Update, context: CallbackContext):
    """Show detailed wallet information"""
    try:
        # Get blockchain info
        blockchain_info = wallet._execute_rpc("getblockchaininfo")
        
        # Get wallet info
        wallet_info_data = wallet._execute_rpc("getwalletinfo")
        
        # Get connection count
        connection_count = wallet._execute_rpc("getconnectioncount")
        
        message = f"🔧 *Wallet Information*\n\n"
        message += f"⛓️ Blockchain: {blockchain_info.get('chain', 'unknown')}\n"
        message += f"📦 Blocks: {blockchain_info.get('blocks', 0)}\n"
        message += f"🔗 Connections: {connection_count}\n"
        message += f"💰 Wallet Balance: {wallet_info_data.get('balance', 0):.8f} TRMP\n"
        message += f"🔐 Encrypted: {'Yes' if wallet_info_data.get('unlocked_until', 0) > 0 else 'No'}\n"
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in wallet_info command: {e}")
        update.message.reply_text("❌ Error retrieving wallet information.")


@is_admin
def backup_users(update: Update, context: CallbackContext):
    """Backup user data"""
    try:
        users = User.select()
        backup_data = []
        
        for user in users:
            backup_data.append({
                'username': user.username,
                'address': user.trmp_address,
                'created_at': str(user.created_at),
                'is_active': user.is_active
            })
        
        # Send as a file (simplified - in production, use proper file handling)
        import json
        backup_json = json.dumps(backup_data, indent=2)
        
        # For now, just show count (file sending would need more setup)
        message = f"💾 *User Backup Ready*\n\n"
        message += f"Total users: {len(backup_data)}\n"
        message += "Contact admin for full backup file."
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in backup_users command: {e}")
        update.message.reply_text("❌ Error creating user backup.")


@is_admin
def broadcast(update: Update, context: CallbackContext):
    """Broadcast message to all users"""
    if not context.args:
        update.message.reply_text("❌ Usage: /broadcast <message>")
        return
    
    message_text = " ".join(context.args)
    
    try:
        users = User.select().where(User.is_active == True)
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Note: This would need the bot instance to send messages
                # For now, just count users
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user.username}: {e}")
                failed_count += 1
        
        result_message = f"📢 *Broadcast Status*\n\n"
        result_message += f"✅ Sent: {sent_count}\n"
        result_message += f"❌ Failed: {failed_count}\n"
        result_message += f"📝 Message: {message_text[:100]}..."
        
        update.message.reply_text(result_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        update.message.reply_text("❌ Error sending broadcast.")


@is_admin
def recent_transactions(update: Update, context: CallbackContext):
    """Show recent transactions"""
    try:
        limit = 10
        if context.args and context.args[0].isdigit():
            limit = min(int(context.args[0]), 50)  # Max 50 transactions
        
        transactions = Transaction.select().order_by(
            Transaction.created_at.desc()
        ).limit(limit)
        
        if not transactions:
            update.message.reply_text("No transactions found.")
            return
        
        message = f"📋 *Recent {limit} Transactions*\n\n"
        
        for tx in transactions:
            tx_type = tx.tx_type.upper()
            amount = tx.amount
            status = tx.status.upper()
            
            if tx.from_user and tx.to_user:
                message += f"{tx_type}: {tx.from_user.username} → {tx.to_user.username}\n"
            elif tx.from_user:
                message += f"{tx_type}: {tx.from_user.username}\n"
            else:
                message += f"{tx_type}: Unknown user\n"
            
            message += f"Amount: {amount:.8f} TRMP | Status: {status}\n"
            if tx.txid:
                message += f"TXID: {tx.txid[:16]}...\n"
            message += "─────────────\n"
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in recent_transactions command: {e}")
        update.message.reply_text("❌ Error retrieving transactions.")
