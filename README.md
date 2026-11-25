# TIWARI AI VIDEO CREATOR

Telegram video bot with credit accounting, manual UPI payment approval, private owner controls, SQLite storage, optional Google Sheets audit logs, Veo generation and FFmpeg clip assembly.

## Included
- 200 first-user credits by default; short video 8 seconds / 50 credits; long video 3 minutes / 75 credits.
- Owner account has unlimited free generation.
- UPI QR payment request; screenshot is sent only to configured OWNER_CHAT_ID.
- Payment screenshot is never treated as confirmed payment. Only owner approval grants credits.
- Owner controls for UPI, subscription price/credits/days, video credit costs/durations, welcome credits, user lookup and manual credit adjustments.
- SQLite operational database plus optional Google Sheets tabs: Users, Videos, Payments, Transactions, Subscriptions.

## Veo access warning
Uses Google's `google-genai` SDK `models.generate_videos`. A Gemini API key alone does not guarantee Veo access. Access depends on API platform, project, model availability, billing and any allowlisting. If Google returns 403/404, enable Veo for your supported Google project/platform. See https://github.com/googleapis/python-genai and https://github.com/google/skills/blob/main/skills/cloud/gemini-api/references/media_generation.md

Long outputs are made by generating multiple clips and joining them with FFmpeg. Visual continuity can vary; every clip may incur separate provider charges. Check Google's pricing before offering long videos commercially.

## Termux
```bash
pkg update -y && pkg upgrade -y
pkg install python git ffmpeg -y
git clone https://github.com/coodwithyogesh-blip/video-bot-veo.git
cd video-bot-veo
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
python -m pytest -q
python main.py
```
Set TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, OWNER_USER_ID and OWNER_CHAT_ID in local `.env`. Do not share or commit it.

## Google Sheets
1. Create a Google Cloud project and enable Google Sheets API.
2. Create a service account and download its JSON key to this folder as `service-account.json`.
3. Create a spreadsheet and share it with the service-account email as Editor.
4. Put its ID in `GOOGLE_SHEET_ID` in `.env`.
5. Keep the JSON private. Without Sheets credentials, SQLite continues to work.

## Owner commands (only owner IDs in private owner chat)
- `/owner` dashboard; `/user USER_ID` lookup
- `/setupi yourname@upi`; `/setprice 99`
- `/setshortcost 50`; `/setlongcost 75`
- `/setshortseconds 8`; `/setlongminutes 3`; `/setwelcome 200`
- `/setsubcredits 500`; `/setsubdays 30`
- `/addcredits USER_ID AMOUNT` (negative removes credits)
- Send QR image with caption exactly `/setqr` to upload/update UPI QR.

## Payment safety
After payment, user taps Complete Payment and uploads screenshot. Bot forwards proof to owner chat only. Check actual UPI/bank settlement before Approve. Each request can only be reviewed once.

## Important status
Files are committed but not live-tested with your Telegram credentials, Google Sheet, QR or a Veo-enabled project. Run tests and a private end-to-end test before accepting payments. The service-account JSON and QR image must stay on your device, not in GitHub.
