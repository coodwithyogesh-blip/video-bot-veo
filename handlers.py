from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import Settings, is_owner


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Welcome to TIWARI AI VIDEO CREATOR.\n"
            "Send /help to see available commands."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Commands:\n/start - Start bot\n/help - Help\n/owner - Private owner panel"
        )


async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat or not is_owner(user.id, chat.id, settings):
        if update.effective_message:
            await update.effective_message.reply_text("Access denied.")
        return

    keyboard = [[InlineKeyboardButton("Owner Settings (setup in next module)", callback_data="owner_settings")]]
    if update.effective_message:
        await update.effective_message.reply_text(
            "OWNER PANEL — private access confirmed.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
