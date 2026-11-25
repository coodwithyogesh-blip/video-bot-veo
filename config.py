import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def required(name):
    value=os.getenv(name,"").strip()
    if not value or value.startswith("PASTE_"):
        raise ValueError(f"Missing required environment variable: {name}")
    return value

@dataclass(frozen=True)
class Settings:
    telegram_bot_token:str
    gemini_api_key:str
    owner_user_id:int
    owner_chat_id:int
    welcome_credits:int
    short_video_seconds:int
    short_video_credits:int
    long_video_minutes:int
    long_video_credits:int
    video_model:str
    google_sheet_id:str
    google_credentials:str
    upi_id:str
    subscription_price:int
    subscription_credits:int
    subscription_days:int
    payment_qr_path:str
    database_path:str
    video_output_dir:str

def load_settings():
    return Settings(
        telegram_bot_token=required("TELEGRAM_BOT_TOKEN"),
        gemini_api_key=required("GEMINI_API_KEY"),
        owner_user_id=int(required("OWNER_USER_ID")),
        owner_chat_id=int(required("OWNER_CHAT_ID")),
        welcome_credits=int(os.getenv("WELCOME_CREDITS","200")),
        short_video_seconds=int(os.getenv("SHORT_VIDEO_SECONDS","8")),
        short_video_credits=int(os.getenv("SHORT_VIDEO_CREDITS","50")),
        long_video_minutes=int(os.getenv("LONG_VIDEO_MINUTES","3")),
        long_video_credits=int(os.getenv("LONG_VIDEO_CREDITS","75")),
        video_model=os.getenv("VIDEO_MODEL","veo-3.1-fast-generate-001"),
        google_sheet_id=os.getenv("GOOGLE_SHEET_ID","").strip(),
        google_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS","service-account.json"),
        upi_id=os.getenv("UPI_ID",""),
        subscription_price=int(os.getenv("SUBSCRIPTION_PRICE","99")),
        subscription_credits=int(os.getenv("SUBSCRIPTION_CREDITS","500")),
        subscription_days=int(os.getenv("SUBSCRIPTION_DAYS","30")),
        payment_qr_path=os.getenv("PAYMENT_QR_PATH","payment_qr.png"),
        database_path=os.getenv("DATABASE_PATH","tiwari_bot.sqlite3"),
        video_output_dir=os.getenv("VIDEO_OUTPUT_DIR","generated_videos"),
    )

def is_owner(user_id,chat_id,settings):
    return bool(user_id is not None and chat_id is not None and
        user_id==settings.owner_user_id and chat_id==settings.owner_chat_id and chat_id>0)
