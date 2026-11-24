from datetime import datetime, timezone, timedelta
from email.utils import parseaddr
from database import all_leads, get_lead, update_lead, add_reply
from google_services import send_email, list_recent_messages
from claude_agent import classify_reply, generate_email
from config import FOLLOWUP1_DAYS, FOLLOWUP2_DAYS

def approve_and_send(lead_id, subject, body):
    lead = get_lead(lead_id)
    if not lead or not lead.get("email"):
        raise ValueError("Lead or email address missing.")
    if lead.get("opt_out"):
        raise ValueError("This lead opted out; sending is blocked.")
    result = send_email(lead["email"], subject, body)
    now = datetime.now(timezone.utc).isoformat()
    update_lead(lead_id, status="Email Sent", initial_subject=subject,
                initial_body=body, last_sent_at=now, followup_count=0,
                last_gmail_thread_id=result.get("threadId"))
    return result

def process_replies():
    messages = list_recent_messages()
    leads = all_leads()
    processed = []
    for msg in messages:
        sender = parseaddr(msg["from"])[1].lower()
        lead = next((x for x in leads if (x.get("email") or "").lower()==sender), None)
        if not lead or not msg["body"]:
            continue
        result = classify_reply(lead, msg["body"])
        label = result.get("classification","other")
        if label == "opt_out":
            update_lead(lead["id"], status="Not Interested", opt_out=1)
        elif label == "not_interested":
            update_lead(lead["id"], status="Not Interested")
        elif label in ("interested","pricing","collaboration_request"):
            update_lead(lead["id"], status="Interested")
        add_reply(lead["id"], msg["id"], msg["date"], label, msg["body"],
                  result.get("suggested_reply",""))
        processed.append({"lead":lead["name"],"classification":label,"draft":result.get("suggested_reply","")})
    return processed

def due_followups(now=None):
    now = now or datetime.now(timezone.utc)
    sent = []
    for lead in all_leads():
        if lead["status"] not in ("Email Sent","Follow-up Due") or lead["opt_out"] or not lead["last_sent_at"]:
            continue
        try: last = datetime.fromisoformat(lead["last_sent_at"])
        except Exception: continue
        days = (now-last).total_seconds()/86400
        count = int(lead["followup_count"] or 0)
        due = (count == 0 and days >= FOLLOWUP1_DAYS) or (count == 1 and days >= FOLLOWUP2_DAYS)
        if due:
            sent.append({"id":lead["id"],"name":lead["name"],"days":round(days,1),"count":count})
    return sent

def send_followup(lead_id, campaign_brief):
    lead = get_lead(lead_id)
    if not lead or lead["opt_out"] or lead["status"] not in ("Email Sent","Follow-up Due"):
        raise ValueError("Follow-up is not permitted for this lead.")
    if int(lead["followup_count"] or 0) >= 2:
        raise ValueError("Maximum follow-ups already sent.")
    draft = generate_email(lead, campaign_brief, kind="follow-up", previous_email=lead.get("initial_body",""))
    # Explicit human approval is required in the dashboard before this function is called.
    result = send_email(lead["email"], draft["subject"], draft["body"], lead.get("last_gmail_thread_id"))
    update_lead(lead_id, status="Follow-up Due", last_sent_at=datetime.now(timezone.utc).isoformat(),
                followup_count=int(lead["followup_count"] or 0)+1,
                last_gmail_thread_id=result.get("threadId"))
    return draft
