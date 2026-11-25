from config import Settings, is_owner


def settings():
    return Settings(
        telegram_bot_token="token",
        gemini_api_key="key",
        owner_user_id=111,
        owner_chat_id=222,
        welcome_credits=200,
        short_video_seconds=8,
        short_video_credits=50,
        long_video_minutes=3,
        long_video_credits=75,
        video_model="veo-test",
        google_sheet_id="",
        google_credentials="service-account.json",
        upi_id="",
        subscription_price=99,
        subscription_credits=500,
        subscription_days=30,
        payment_qr_path="payment_qr.png",
        database_path=":memory:",
        video_output_dir="generated_videos",
    )


def test_owner_requires_both_user_and_chat_ids():
    assert is_owner(111, 222, settings()) is True
    assert is_owner(111, 999, settings()) is False
    assert is_owner(999, 222, settings()) is False
    assert is_owner(None, 222, settings()) is False
    assert is_owner(111, None, settings()) is False
