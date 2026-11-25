from config import Settings, is_owner


def settings():
    return Settings(
        telegram_bot_token="token",
        gemini_api_key="key",
        owner_user_id=111,
        owner_chat_id=222,
    )


def test_owner_requires_both_user_and_chat_ids():
    assert is_owner(111, 222, settings()) is True
    assert is_owner(111, 999, settings()) is False
    assert is_owner(999, 222, settings()) is False
    assert is_owner(None, 222, settings()) is False
    assert is_owner(111, None, settings()) is False
