import logging
from telegram.ext import Application, CommandHandler

from config import load_settings
from handlers import start_command, help_command, owner_command

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)


def main() -> None:
    settings = load_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("owner", owner_command))

    logging.info("TIWARI AI VIDEO CREATOR is starting")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
