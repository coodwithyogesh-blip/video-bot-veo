import os, asyncio
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, NetworkError
import logging
from config import is_owner
from video_generator import generate_video

def db(c): return c.application.bot_data["db"]
def sheets(c): return c.application.bot_data["sheets"]
def owner_ok(u,c):
    return bool(u.effective_user and u.effective_chat and
        is_owner(u.effective_user.id,u.effective_chat.id,c.application.bot_data["settings"]))
def setting(c,k,d): return db(c).get_setting(k,str(d))

async def start_command(u,c):
    user=u.effective_user
    if not user or not u.effective_chat: return
    fresh=db(c).ensure_user(user.id,user.username or "",user.first_name or "")
    if fresh:
        stamp=datetime.now(timezone.utc).isoformat()
        sheets(c).append("Users",[user.id,user.username or "",user.first_name or "",stamp])
        sheets(c).append("Transactions",["",user.id,c.application.bot_data["settings"].welcome_credits,"welcome_bonus",c.application.bot_data["settings"].welcome_credits,stamp])
    credits="Unlimited (Owner)" if owner_ok(u,c) else db(c).get_user(user.id)["credits"]
    kb=[[InlineKeyboardButton("🎬 Short Video",callback_data="duration:short"),InlineKeyboardButton("🎞 2–3 Minute Video",callback_data="duration:long")],
        [InlineKeyboardButton("💳 Buy Subscription",callback_data="buy"),InlineKeyboardButton("👛 My Credits",callback_data="balance")]]
    await u.effective_message.reply_text(f"Welcome to TIWARI AI VIDEO CREATOR!\nCredits: {credits}\nChoose video type:",reply_markup=InlineKeyboardMarkup(kb))

async def help_command(u,c):
    await u.effective_message.reply_text("Use /start, /balance and /buy. Owner: /owner, /setupi UPI, /setprice 99, /setshortcost 50, /setlongcost 75, /setsubcredits 500, /setsubdays 30, /addcredits USER_ID AMOUNT. Send QR photo with caption /setqr.")

async def balance_command(u,c):
    if owner_ok(u,c): return await u.effective_message.reply_text("Owner: unlimited credits.")
    row=db(c).get_user(u.effective_user.id)
    await u.effective_message.reply_text(f"Balance: {row['credits'] if row else 0} credits")

async def send_buy(u,c):
    if owner_ok(u,c): return await u.effective_message.reply_text("Owner ko payment ki zarurat nahi.")
    user=u.effective_user
    db(c).ensure_user(user.id,user.username or "",user.first_name or "")
    s=c.application.bot_data["settings"]
    amount=int(setting(c,"subscription_price",s.subscription_price))
    upi=setting(c,"upi_id",s.upi_id)
    pid=db(c).create_payment(user.id,amount)
    c.user_data["payment_id"]=pid
    qr=setting(c,"qr_path",s.payment_qr_path)
    msg=f"Subscription: ₹{amount}\nUPI ID: {upi or 'Owner has not configured UPI'}\nRequest: {pid}\nPay using QR/UPI, then tap Complete Payment."
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Complete Payment",callback_data="payment:complete")]])
    if qr and os.path.isfile(qr):
        with open(qr,"rb") as f: await u.effective_message.reply_photo(photo=f,caption=msg,reply_markup=kb)
    else: await u.effective_message.reply_text(msg+"\nQR not uploaded yet.",reply_markup=kb)

async def buy_command(u,c): await send_buy(u,c)

async def owner_command(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    s=db(c).stats()
    kb=[[InlineKeyboardButton("📊 Stats",callback_data="owner:stats"),InlineKeyboardButton("💰 Pending payments",callback_data="owner:payments")],
        [InlineKeyboardButton("⚙️ Settings help",callback_data="owner:settings")]]
    await u.effective_message.reply_text(f"OWNER PANEL\nUsers: {s['users']}\nVideos: {s['videos']}\nCredits used: {s['credits_used']}\nPending: {s['pending']}\nRevenue: ₹{s['revenue']}",reply_markup=InlineKeyboardMarkup(kb))

async def setprice(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=1 or not c.args[0].isdigit(): return await u.effective_message.reply_text("Usage: /setprice 99")
    db(c).set_setting("subscription_price",c.args[0]); await u.effective_message.reply_text("Subscription price updated.")

async def setupi(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    value=" ".join(c.args).strip()
    if not value or len(value)>100: return await u.effective_message.reply_text("Usage: /setupi name@upi")
    db(c).set_setting("upi_id",value); await u.effective_message.reply_text("UPI ID updated.")

async def setcost(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=1 or not c.args[0].isdigit(): return await u.effective_message.reply_text("Usage: /setshortcost 50 or /setlongcost 75")
    key="short_video_credits" if u.effective_message.text.startswith("/setshortcost") else "long_video_credits"
    db(c).set_setting(key,c.args[0]); await u.effective_message.reply_text(f"{key} updated.")

async def setplan(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=1 or not c.args[0].isdigit() or int(c.args[0])<1: return await u.effective_message.reply_text("Usage: /setsubcredits 500 or /setsubdays 30")
    key="subscription_credits" if u.effective_message.text.startswith("/setsubcredits") else "subscription_days"
    db(c).set_setting(key,c.args[0]); await u.effective_message.reply_text(f"{key} updated.")

async def setgeneral(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=1 or not c.args[0].isdigit() or int(c.args[0])<1:
        return await u.effective_message.reply_text("Use /setwelcome 200, /setshortseconds 8, or /setlongminutes 3")
    cmd=u.effective_message.text.split()[0].split("@")[0]
    key={" /setwelcome":"welcome_credits","/setwelcome":"welcome_credits",
         "/setshortseconds":"short_video_seconds","/setlongminutes":"long_video_minutes"}.get(cmd)
    if not key: return await u.effective_message.reply_text("Unknown setting.")
    db(c).set_setting(key,c.args[0])
    await u.effective_message.reply_text(f"{key} updated. Note: welcome credit change applies to new users only.")

async def users_command(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    with db(c).connect() as conn:
        rows=conn.execute("SELECT user_id,username,credits FROM users ORDER BY created_at DESC LIMIT 30").fetchall()
    if not rows: return await u.effective_message.reply_text("No users yet.")
    lines=["Latest users (max 30):"]
    lines.extend(f"{r['user_id']} | @{r['username']} | {r['credits']} credits" for r in rows)
    await u.effective_message.reply_text("\\n".join(lines))

async def user_command(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=1 or not c.args[0].isdigit(): return await u.effective_message.reply_text("Usage: /user TELEGRAM_USER_ID")
    row=db(c).get_user(int(c.args[0]))
    if not row: return await u.effective_message.reply_text("User not found.")
    await u.effective_message.reply_text(f"User: {row['user_id']}\\nUsername: @{row['username']}\\nCredits: {row['credits']}\\nJoined: {row['created_at']}")

async def addcredits(u,c):
    if not owner_ok(u,c): return await u.effective_message.reply_text("Access denied.")
    if len(c.args)!=2: return await u.effective_message.reply_text("Usage: /addcredits USER_ID AMOUNT")
    try:
        uid,amount=int(c.args[0]),int(c.args[1])
        if amount==0: raise ValueError("Amount cannot be zero")
        balance=db(c).change_credits(uid,amount,"owner_adjustment")
        sheets(c).append("Transactions",["",uid,amount,"owner_adjustment",balance,datetime.now(timezone.utc).isoformat()])
        await u.effective_message.reply_text(f"User {uid}: balance {balance}")
        await c.bot.send_message(uid,f"Owner updated your credits. Balance: {balance}")
    except Exception as e: await u.effective_message.reply_text(f"Error: {e}")

async def callbacks(u,c):
    q=u.callback_query
    if not q: return
    # Telegram callback IDs expire; an expired spinner answer must not crash the handler.
    try:
        await q.answer()
    except BadRequest as exc:
        if "too old" not in str(exc).lower() and "query id is invalid" not in str(exc).lower():
            raise
        logging.warning("Telegram callback expired; continuing callback processing.")
    except NetworkError as exc:
        # A temporary Telegram timeout must not prevent the actual button action.
        logging.warning("Could not acknowledge callback due to network issue; continuing: %s", type(exc).__name__)
    data=q.data or ""
    if data.startswith(("owner:","payok:","payno:")) and not owner_ok(u,c):
        return await q.edit_message_text("Access denied.")
    if data.startswith("duration:"):
        c.user_data["video_mode"]=data.split(":")[1]; c.user_data["awaiting"]="prompt"
        await q.message.reply_text("Apna video prompt bhejo.")
    elif data=="buy": await send_buy(u,c)
    elif data=="balance":
        row=db(c).get_user(u.effective_user.id)
        await q.message.reply_text("Owner: unlimited." if owner_ok(u,c) else f"Balance: {row['credits'] if row else 0}")
    elif data=="payment:complete":
        if not c.user_data.get("payment_id"): await q.message.reply_text("Pehle /buy se request banao.")
        else: c.user_data["awaiting"]="proof"; await q.message.reply_text("Ab payment screenshot upload karo.")
    elif data=="owner:stats": await q.message.reply_text(str(db(c).stats()))
    elif data=="owner:settings":
        await q.message.reply_text("Commands: /setupi UPI_ID, /setprice 99, /setshortcost 50, /setlongcost 75, /setshortseconds 8, /setlongminutes 3, /setwelcome 200, /setsubcredits 500, /setsubdays 30, /users, /user USER_ID, /addcredits USER_ID AMOUNT. QR photo caption /setqr.")
    elif data=="owner:payments":
        rows=db(c).pending_payments()
        if not rows: return await q.message.reply_text("No pending payments.")
        for p in rows:
            kb=[[InlineKeyboardButton("Approve",callback_data=f"payok:{p['payment_id']}"),InlineKeyboardButton("Reject",callback_data=f"payno:{p['payment_id']}")]]
            await q.message.reply_text(f"Payment {p['payment_id']}\nUser {p['user_id']}\n₹{p['amount']}",reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith(("payok:","payno:")):
        pid=data.split(":")[1]; approved=data.startswith("payok:")
        result=db(c).review_payment(pid,approved)
        if not result: return await q.message.reply_text("Already reviewed or not found.")
        p=result["payment"]
        sheets(c).append("Payments",[pid,p["user_id"],p["amount"],"approved" if approved else "rejected",p["proof_file_id"],p["created_at"],datetime.now(timezone.utc).isoformat()])
        if approved:
            stamp=datetime.now(timezone.utc).isoformat()
            sheets(c).append("Transactions",["",p["user_id"],result["credits"],"subscription_payment",result["balance"],stamp])
            sheets(c).append("Subscriptions",["",p["user_id"],"credit_subscription",result["credits"],result["starts_at"],result["expires_at"],pid])
            notified=True
            try:
                await c.bot.send_message(p["user_id"],f"Payment approved. {result['credits']} credits added. Balance: {result['balance']}.")
            except NetworkError:
                notified=False
                logging.warning("Payment %s approved in database, but user notification failed.", pid)
            await q.message.reply_text(
                f"Approved; {result['credits']} credits granted. " +
                ("User notified." if notified else "User notification failed; credits are already added.")
            )
        else:
            notified=True
            try:
                await c.bot.send_message(p["user_id"],"Payment rejected. Contact owner.")
            except NetworkError:
                notified=False
                logging.warning("Payment %s rejected in database, but user notification failed.", pid)
            await q.message.reply_text("Payment rejected." if notified else "Payment rejected in database; user notification failed.")

async def photos(u,c):
    user=u.effective_user; msg=u.effective_message
    if not user or not msg or not msg.photo: return
    if owner_ok(u,c) and (msg.caption or "").strip().lower()=="/setqr":
        s=c.application.bot_data["settings"]; path=s.payment_qr_path
        f=await c.bot.get_file(msg.photo[-1].file_id); await f.download_to_drive(path)
        db(c).set_setting("qr_path",path); return await msg.reply_text("QR image updated.")
    if c.user_data.get("awaiting")!="proof": return await msg.reply_text("Pehle /buy aur Complete Payment dabao.")
    pid=c.user_data.get("payment_id"); p=db(c).get_payment(pid) if pid else None
    if not p or p["status"]!="awaiting_proof": return await msg.reply_text("Payment request invalid. /buy se dobara start karo.")
    photo=msg.photo[-1]; db(c).attach_proof(pid,photo.file_id)
    sheets(c).append("Payments",[pid,user.id,p["amount"],"pending",photo.file_id,p["created_at"],""])
    s=c.application.bot_data["settings"]
    caption=f"PAYMENT PROOF — VERIFY MANUALLY\nID: {pid}\nUser: {user.id}\nAmount: ₹{p['amount']}\nScreenshot is NOT proof of settlement."
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Approve",callback_data=f"payok:{pid}"),InlineKeyboardButton("Reject",callback_data=f"payno:{pid}")]])
    await c.bot.send_photo(s.owner_chat_id,photo=photo.file_id,caption=caption,reply_markup=kb)
    c.user_data["awaiting"]=None
    await msg.reply_text("Screenshot sirf Owner ko verification ke liye bheja gaya. Approval ke baad credits milenge.")

async def texts(u,c):
    msg=u.effective_message; user=u.effective_user
    if not msg or not msg.text or not user or c.user_data.get("awaiting")!="prompt": return
    prompt=msg.text.strip()
    if len(prompt)<5 or len(prompt)>1500: return await msg.reply_text("Prompt 5–1500 characters ka hona chahiye.")
    s=c.application.bot_data["settings"]; mode=c.user_data.get("video_mode","short")
    seconds=int(setting(c,"short_video_seconds",s.short_video_seconds)) if mode=="short" else int(setting(c,"long_video_minutes",s.long_video_minutes))*60
    cost=int(setting(c,"short_video_credits",s.short_video_credits) if mode=="short" else setting(c,"long_video_credits",s.long_video_credits))
    db(c).ensure_user(user.id,user.username or "",user.first_name or "")
    free=owner_ok(u,c)
    if not free:
        row=db(c).get_user(user.id)
        if row["credits"]<cost:
            c.user_data["awaiting"]=None
            return await msg.reply_text(f"Credits kam hain. Required {cost}, available {row['credits']}. /buy use karo.")
        db(c).change_credits(user.id,-cost,f"video_{mode}")
    c.user_data["awaiting"]=None
    status=await msg.reply_text("Video generation started. Long video mein kaafi samay lag sakta hai.")
    try:
        path=await asyncio.to_thread(generate_video,s.gemini_api_key,s.video_model,prompt,seconds,s.video_output_dir)
        db(c).record_video(user.id,prompt,seconds,0 if free else cost,path,"completed")
        if not free: sheets(c).append("Transactions",["",user.id,-cost,f"video_{mode}",db(c).get_user(user.id)["credits"],datetime.now(timezone.utc).isoformat()])
        sheets(c).append("Videos",[user.id,prompt,seconds,0 if free else cost,path,"completed",datetime.now(timezone.utc).isoformat()])
        with open(path,"rb") as f: await msg.reply_video(video=f,caption="Your video is ready!")
        if not free: await msg.reply_text(f"Remaining credits: {db(c).get_user(user.id)['credits']}")
    except Exception as e:
        if not free:
            balance=db(c).change_credits(user.id,cost,"generation_refund")
            sheets(c).append("Transactions",["",user.id,cost,"generation_refund",balance,datetime.now(timezone.utc).isoformat()])
        db(c).record_video(user.id,prompt,seconds,0 if free else cost,"","failed")
        await msg.reply_text(f"Generation failed; credits refunded. Check Veo access, billing and quota. Error: {str(e)[:250]}")
    finally:
        try: await status.delete()
        except Exception: pass
