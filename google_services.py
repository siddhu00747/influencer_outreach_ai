import os, base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GOOGLE_OAUTH_CLIENT_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SHEET_ID

SCOPES = [
 "https://www.googleapis.com/auth/gmail.modify",
 "https://www.googleapis.com/auth/gmail.send",
 "https://www.googleapis.com/auth/spreadsheets"
]

def credentials():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_OAUTH_CLIENT_FILE):
                raise FileNotFoundError("Download Google OAuth Desktop credentials as credentials.json.")
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_OAUTH_CLIENT_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

def gmail_service():
    return build("gmail", "v1", credentials=credentials())

def sheets_service():
    return build("sheets", "v4", credentials=credentials())

def send_email(to, subject, body, thread_id=None):
    service = gmail_service()
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw}
    if thread_id: payload["threadId"] = thread_id
    return service.users().messages().send(userId="me", body=payload).execute()

def list_recent_messages(query="in:inbox newer_than:14d", max_results=50):
    svc = gmail_service()
    data = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    out = []
    for item in data.get("messages", []):
        m = svc.users().messages().get(userId="me", id=item["id"], format="full").execute()
        headers = {h["name"].lower():h["value"] for h in m.get("payload",{}).get("headers",[])}
        parts = m.get("payload",{})
        body = _extract_body(parts)
        out.append({"id":m["id"],"thread_id":m.get("threadId"),"from":headers.get("from",""),
                    "subject":headers.get("subject",""),"date":headers.get("date",""),"body":body})
    return out

def _extract_body(payload):
    data = payload.get("body",{}).get("data")
    if data:
        return base64.urlsafe_b64decode(data+"==").decode("utf-8",errors="ignore")
    for part in payload.get("parts",[]):
        if part.get("mimeType") == "text/plain":
            d = part.get("body",{}).get("data")
            if d: return base64.urlsafe_b64decode(d+"==").decode("utf-8",errors="ignore")
        nested = _extract_body(part)
        if nested: return nested
    return ""

def append_lead_to_sheet(lead):
    if not GOOGLE_SHEET_ID:
        return "Skipped: GOOGLE_SHEET_ID not configured"
    svc = sheets_service()
    values = [[lead.get(k,"") for k in ["name","username","profile_url","niche","followers","email","location","score","status"]]]
    svc.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEET_ID, range="Leads!A:I",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values":values}).execute()
    return "Synced"
