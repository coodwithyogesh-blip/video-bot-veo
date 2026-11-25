import sqlite3,uuid
from datetime import datetime,timezone,timedelta

def now(): return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self,path,welcome):
        self.path=path; self.welcome=welcome; self.init()
    def connect(self):
        c=sqlite3.connect(self.path,timeout=30); c.row_factory=sqlite3.Row; return c
    def init(self):
        with self.connect() as c:
            c.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,credits INTEGER NOT NULL,created_at TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS payments(payment_id TEXT PRIMARY KEY,user_id INTEGER,amount INTEGER,status TEXT,proof_file_id TEXT,created_at TEXT,reviewed_at TEXT);
            CREATE TABLE IF NOT EXISTS videos(video_id TEXT PRIMARY KEY,user_id INTEGER,prompt TEXT,seconds INTEGER,credits INTEGER,file_path TEXT,status TEXT,created_at TEXT);
            CREATE TABLE IF NOT EXISTS transactions(tx_id TEXT PRIMARY KEY,user_id INTEGER,amount INTEGER,reason TEXT,balance_after INTEGER,created_at TEXT);
            CREATE TABLE IF NOT EXISTS subscriptions(sub_id TEXT PRIMARY KEY,user_id INTEGER,plan TEXT,credits INTEGER,starts_at TEXT,expires_at TEXT,payment_id TEXT);
            """)
    def ensure_user(self,uid,username,first):
        with self.connect() as c:
            row=c.execute("SELECT user_id FROM users WHERE user_id=?",(uid,)).fetchone()
            if row:
                c.execute("UPDATE users SET username=?,first_name=? WHERE user_id=?",(username,first,uid)); return False
            welcome_row=c.execute("SELECT value FROM settings WHERE key='welcome_credits'").fetchone()
            welcome=int(welcome_row["value"]) if welcome_row else self.welcome
            c.execute("INSERT INTO users VALUES(?,?,?,?,?)",(uid,username,first,welcome,now()))
            c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?)",(uuid.uuid4().hex,uid,welcome,"welcome_bonus",welcome,now()))
            return True
    def get_user(self,uid):
        with self.connect() as c:
            r=c.execute("SELECT * FROM users WHERE user_id=?",(uid,)).fetchone()
            return dict(r) if r else None
    def change_credits(self,uid,amount,reason):
        with self.connect() as c:
            c.execute("INSERT OR IGNORE INTO users VALUES(?,?,?,?,?)",(uid,"","",0,now()))
            balance=c.execute("SELECT credits FROM users WHERE user_id=?",(uid,)).fetchone()[0]+amount
            if balance<0: raise ValueError("Not enough credits")
            c.execute("UPDATE users SET credits=? WHERE user_id=?",(balance,uid))
            c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?)",(uuid.uuid4().hex,uid,amount,reason,balance,now()))
            return balance
    def set_setting(self,k,v):
        with self.connect() as c:
            c.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))
    def get_setting(self,k,default=""):
        with self.connect() as c:
            r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone()
            return r["value"] if r else default
    def create_payment(self,uid,amount):
        pid=uuid.uuid4().hex[:12]
        with self.connect() as c:
            c.execute("INSERT INTO payments VALUES(?,?,?,?,?,?,?)",(pid,uid,amount,"awaiting_proof","",now(),""))
        return pid
    def attach_proof(self,pid,file_id):
        with self.connect() as c:
            c.execute("UPDATE payments SET proof_file_id=?,status='pending' WHERE payment_id=? AND status='awaiting_proof'",(file_id,pid))
    def get_payment(self,pid):
        with self.connect() as c:
            r=c.execute("SELECT * FROM payments WHERE payment_id=?",(pid,)).fetchone()
            return dict(r) if r else None
    def pending_payments(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute("SELECT * FROM payments WHERE status='pending' ORDER BY created_at")]
    def review_payment(self,pid,approved):
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            r=c.execute("SELECT * FROM payments WHERE payment_id=?",(pid,)).fetchone()
            if not r or r["status"]!="pending": return None
            p=dict(r); c.execute("UPDATE payments SET status=?,reviewed_at=? WHERE payment_id=?",("approved" if approved else "rejected",now(),pid))
            if not approved: return {"payment":p,"credits":0}
            credits=int(self.get_setting("subscription_credits","500"))
            days=int(self.get_setting("subscription_days","30"))
            c.execute("UPDATE users SET credits=credits+? WHERE user_id=?",(credits,p["user_id"]))
            bal=c.execute("SELECT credits FROM users WHERE user_id=?",(p["user_id"],)).fetchone()[0]
            stamp=datetime.now(timezone.utc); expiry=stamp+timedelta(days=days)
            c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?)",(uuid.uuid4().hex,p["user_id"],credits,"subscription_payment",bal,now()))
            c.execute("INSERT INTO subscriptions VALUES(?,?,?,?,?,?,?)",(uuid.uuid4().hex,p["user_id"],"credit_subscription",credits,stamp.isoformat(),expiry.isoformat(),pid))
            return {"payment":p,"credits":credits,"balance":bal,"starts_at":stamp.isoformat(),"expires_at":expiry.isoformat()}
    def stats(self):
        with self.connect() as c:
            return {"users":c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "videos":c.execute("SELECT COUNT(*) FROM videos WHERE status='completed'").fetchone()[0],
                "credits_used":-c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE amount<0").fetchone()[0],
                "pending":c.execute("SELECT COUNT(*) FROM payments WHERE status='pending'").fetchone()[0],
                "revenue":c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='approved'").fetchone()[0]}
    def record_video(self,uid,prompt,seconds,cost,path,status):
        with self.connect() as c:
            c.execute("INSERT INTO videos VALUES(?,?,?,?,?,?,?,?)",(uuid.uuid4().hex,uid,prompt,seconds,cost,path,status,now()))
