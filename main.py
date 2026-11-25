import logging
from telegram.ext import Application,CommandHandler,CallbackQueryHandler,MessageHandler,filters
from config import load_settings
from database import Database
from sheets import SheetsLogger
from handlers import start_command,help_command,balance_command,buy_command,owner_command,setprice,setupi,setcost,setplan,addcredits,callbacks,photos,texts

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def main():
    s=load_settings()
    app=Application.builder().token(s.telegram_bot_token).build()
    app.bot_data.update({"settings":s,"db":Database(s.database_path,s.welcome_credits),
                         "sheets":SheetsLogger(s.google_sheet_id,s.google_credentials)})
    for command,fn in [("start",start_command),("help",help_command),("balance",balance_command),
        ("buy",buy_command),("owner",owner_command),("setprice",setprice),("setupi",setupi),
        ("setshortcost",setcost),("setlongcost",setcost),("setsubcredits",setplan),
        ("setsubdays",setplan),("addcredits",addcredits)]:
        app.add_handler(CommandHandler(command,fn))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.PHOTO,photos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,texts))
    logging.info("TIWARI AI VIDEO CREATOR starting")
    app.run_polling()

if __name__=="__main__": main()
