"""
Telegram Bot for Chip Warden
Sends notifications and handles commands
"""

import os
from typing import Optional
from pathlib import Path

try:
    import telegram
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Telegram features disabled.")


class TelegramNotifier:
    """Handles Telegram notifications for Chip Warden"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot

        Args:
            bot_token: Bot token from @BotFather
            chat_id: Your Telegram chat ID
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)

    async def send_message(self, message: str, parse_mode: str = 'Markdown'):
        """
        Send a message to the configured chat

        Args:
            message: Message text (supports Markdown)
            parse_mode: 'Markdown' or 'HTML'
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    async def notify_new_file(
        self,
        project: str,
        part: str,
        version: int,
        setup: str,
        machine: str,
        tools: int,
        warnings: list = None
    ):
        """Notify about new G-code file posted"""
        message = f"🔧 *New Program Posted*\n\n"
        message += f"📦 *Part:* {part} (v{version})\n"
        message += f"📁 *Project:* {project}\n"
        message += f"⚙️ *Setup:* {setup}\n"
        message += f"🏭 *Machine:* {machine}\n"
        message += f"🔨 *Tools:* {tools}\n\n"

        if warnings:
            message += "⚠️ *Warnings:*\n"
            for warning in warnings:
                message += f"  • {warning}\n"
            message += "\n"

        message += "_File ready on FTP - grab it and run!_"

        await self.send_message(message)

    async def notify_cleanup(self, filename: str):
        """Notify that file was cleaned up from FTP"""
        message = f"🗑️ Cleaned up: `{filename}`\n"
        message += "_FTP directory cleaned_"
        await self.send_message(message)

    async def notify_error(self, error_msg: str):
        """Notify about an error"""
        message = f"❌ *Error in Chip Warden*\n\n"
        message += f"```\n{error_msg}\n```"
        await self.send_message(message)

    def send_message_sync(self, message: str):
        """
        Synchronous wrapper for sending messages
        Useful for non-async contexts
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule it
                asyncio.create_task(self.send_message(message))
            else:
                # Run in new loop
                asyncio.run(self.send_message(message))
        except Exception as e:
            print(f"❌ Failed to send message: {e}")


class TelegramCommandBot:
    """
    Telegram bot that responds to commands
    /status - Show Russ status
    /cleanup - Manually trigger FTP cleanup
    /latest [part] - Show latest version of a part
    """

    def __init__(self, bot_token: str, chat_id: str, file_manager=None):
        """
        Initialize command bot

        Args:
            bot_token: Bot token
            chat_id: Authorized chat ID
            file_manager: FileManager instance for commands
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.file_manager = file_manager
        self.app = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 *Russ here - Chip Warden is online*\n\n"
            "Available commands:\n"
            "/status - Show system status\n"
            "/cleanup - Clean up old FTP files\n"
            "/help - Show this message\n\n"
            "_In Russ we trust._",
            parse_mode='Markdown'
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        # Check if message is from authorized chat
        if str(update.effective_chat.id) != self.chat_id:
            await update.message.reply_text("⛔ Unauthorized")
            return

        status = "✅ *Chip Warden Status*\n\n"
        status += "🤖 Russ is running\n"

        if self.file_manager:
            # Count files in FTP
            ftp_files = list(self.file_manager.ftp_dir.glob("*.nc"))
            status += f"📤 FTP files: {len(ftp_files)}\n"

            # Count archived projects
            projects = [d for d in self.file_manager.parts_archive.iterdir() if d.is_dir() and not d.name.startswith('.')]
            status += f"📦 Archived projects: {len(projects)}\n"

        await update.message.reply_text(status, parse_mode='Markdown')

    async def cleanup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cleanup command"""
        if str(update.effective_chat.id) != self.chat_id:
            await update.message.reply_text("⛔ Unauthorized")
            return

        await update.message.reply_text("🗑️ Cleaning up FTP directory...")

        if self.file_manager:
            removed = self.file_manager.cleanup_old_ftp_files(keep_count=1)
            await update.message.reply_text(
                f"✅ Removed {removed} old files from FTP",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ File manager not available")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    def start_bot(self):
        """Start the Telegram bot (blocking)"""
        self.app = Application.builder().token(self.bot_token).build()

        # Add command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("cleanup", self.cleanup_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        print("🤖 Telegram bot started. Send /start to begin.")
        self.app.run_polling()


def load_telegram_token(config_dir: str = "russ/config") -> Optional[str]:
    """
    Load Telegram bot token from file or environment

    Checks:
    1. Environment variable TELEGRAM_BOT_TOKEN
    2. File: config/telegram.token

    Returns:
        Token string or None
    """
    # Check environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        return token

    # Check file
    token_file = Path(config_dir) / "telegram.token"
    if token_file.exists():
        return token_file.read_text().strip()

    return None


if __name__ == "__main__":
    import asyncio

    # Test with dummy token/chat (won't actually send)
    token = load_telegram_token()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '123456789')

    if not token:
        print("⚠️ No Telegram token found. Set TELEGRAM_BOT_TOKEN or create config/telegram.token")
    elif not TELEGRAM_AVAILABLE:
        print("⚠️ Install python-telegram-bot: pip install python-telegram-bot")
    else:
        print("✅ Telegram bot configured")
        print(f"   Token: {token[:10]}...")
        print(f"   Chat ID: {chat_id}")

        # Test notification (won't send without valid token)
        # notifier = TelegramNotifier(token, chat_id)
        # asyncio.run(notifier.notify_new_file(
        #     project="test-project",
        #     part="1001",
        #     version=2,
        #     setup="OP1-TEST",
        #     machine="PUMA",
        #     tools=5
        # ))
