# TIWARI AI VIDEO CREATOR

Telegram video-generation bot starter project. Owner identity and all adjustable credit/video settings are configured through a local `.env` file.

## Security

- Set both `OWNER_USER_ID` and `OWNER_CHAT_ID` in `.env`.
- The `/owner` command requires both values to match the Telegram user and chat.
- Never upload `.env`, API keys, or service-account credentials to GitHub.
- Payment screenshots must be treated as unverified evidence. Credits should only be granted after manual owner approval.

## Termux setup

```bash
pkg update -y && pkg upgrade -y
pkg install python git ffmpeg -y
git clone https://github.com/coodwithyogesh-blip/video-bot-veo.git
cd video-bot-veo
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

Fill the real values in `.env` before running the bot. Do not paste tokens into chat or commit `.env`.

## Current implementation stage

The repository currently contains the secure bot foundation and owner-ID checks. Credit ledger, Google Sheets persistence, payment verification, and the actual video-generation workflow are separate implementation stages and are not yet complete.

## Video API note

Video generation availability depends on the Google product, project, billing, and model access enabled for your account. Verify your selected Google video API before expecting a Gemini API key alone to work. See the official Google Cloud video-generation guide: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-text
