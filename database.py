import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).with_name("outreach.db")

def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, username TEXT UNIQUE, profile_url TEXT, niche TEXT,
            followers INTEGER DEFAULT 0, email TEXT, location TEXT,
            summary TEXT, score INTEGER DEFAULT 0, status TEXT DEFAULT 'New Lead',
            initial_subject TEXT, initial_body TEXT, created_at TEXT,
            last_sent_at TEXT, followup_count INTEGER DEFAULT 0,
            last_gmail_thread_id TEXT, opt_out INTEGER DEFAULT 0,
            notes TEXT
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER, gmail_message_id TEXT UNIQUE, received_at TEXT,
            classification TEXT, body TEXT, suggested_reply TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )""")
        con.commit()

def upsert_lead(row):
    now = datetime.now(timezone.utc).isoformat()
    username = (row.get("username") or "").strip().lstrip("@")
    if not username:
        raise ValueError("Instagram username is required.")
    with connect() as con:
        existing = con.execute("SELECT id FROM leads WHERE username=?", (username,)).fetchone()
        vals = (
            row.get("name",""), username, row.get("profile_url",""), row.get("niche",""),
            int(row.get("followers") or 0), row.get("email",""), row.get("location",""),
            row.get("summary",""), int(row.get("score") or 0),
        )
        if existing:
            con.execute("""UPDATE leads SET name=?,profile_url=?,niche=?,followers=?,email=?,
                location=?,summary=?,score=? WHERE username=?""",
                (vals[0], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], vals[8], username))
            lead_id = existing["id"]
        else:
            cur = con.execute("""INSERT INTO leads
                (name,username,profile_url,niche,followers,email,location,summary,score,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,'New Lead',?)""", vals + (now,))
            lead_id = cur.lastrowid
        con.commit()
        return lead_id

def all_leads():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM leads ORDER BY score DESC, id DESC")]

def get_lead(lead_id):
    with connect() as con:
        r = con.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return dict(r) if r else None

def update_lead(lead_id, **fields):
    allowed = {"status","initial_subject","initial_body","last_sent_at","followup_count",
               "last_gmail_thread_id","opt_out","notes","score","summary"}
    fields = {k:v for k,v in fields.items() if k in allowed}
    if not fields: return
    sql = ", ".join(f"{k}=?" for k in fields)
    with connect() as con:
        con.execute(f"UPDATE leads SET {sql} WHERE id=?", tuple(fields.values())+(lead_id,))
        con.commit()

def add_reply(lead_id, message_id, received_at, classification, body, suggested_reply):
    with connect() as con:
        con.execute("""INSERT OR IGNORE INTO replies
        (lead_id,gmail_message_id,received_at,classification,body,suggested_reply)
        VALUES (?,?,?,?,?,?)""", (lead_id,message_id,received_at,classification,body,suggested_reply))
        con.commit()

def get_replies():
    with connect() as con:
        return [dict(r) for r in con.execute("""SELECT replies.*, leads.name, leads.username
          FROM replies LEFT JOIN leads ON leads.id=replies.lead_id ORDER BY replies.id DESC""")]
