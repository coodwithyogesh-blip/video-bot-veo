import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    owner_user_id: int
    owner_chat_id: int
    welcome_credits: int = 200
    short_video_seconds: int = 8
    short_video_credits: int = 50
    long_video_minutes: int = 3
    long_video_credits: int = 75
    video_model: str = "veo-3.1-fast-generate-001"


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("PASTE_"):
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
        gemini_api_key=_required("GEMINI_API_KEY"),
        owner_user_id=int(_required("OWNER_USER_ID")),
        owner_chat_id=int(_required("OWNER_CHAT_ID")),
        welcome_credits=int(os.getenv("WELCOME_CREDITS", "200")),
        short_video_seconds=int(os.getenv("SHORT_VIDEO_SECONDS", "8")),
        short_video_credits=int(os.getenv("SHORT_VIDEO_CREDITS", "50")),
        long_video_minutes=int(os.getenv("LONG_VIDEO_MINUTES", "3")),
        long_video_credits=int(os.getenv("LONG_VIDEO_CREDITS", "75")),
        video_model=os.getenv("VIDEO_MODEL", "veo-3.1-fast-generate-001").strip(),
    )


def is_owner(user_id: int | None, chat_id: int | None, settings: Settings) -> bool:
    """Require both the Telegram account ID and private owner chat ID to match."""
    return (
        user_id is not None
        and chat_id is not None
        and user_id == settings.owner_user_id
        and chat_id == settings.owner_chat_id
    )
