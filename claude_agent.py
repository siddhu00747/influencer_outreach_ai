import json
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, SENDER_COMPANY

def client():
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing. Add it to .env.")
    return Anthropic(api_key=ANTHROPIC_API_KEY)

def _ask(prompt, max_tokens=900):
    msg = client().messages.create(
        model=CLAUDE_MODEL, max_tokens=max_tokens,
        messages=[{"role":"user","content":prompt}]
    )
    return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text").strip()

def analyze_influencer(lead, campaign_brief):
    prompt = f"""You are an influencer campaign research assistant.
Campaign brief: {campaign_brief}
Public profile data: {json.dumps(lead, ensure_ascii=False)}
Return ONLY valid JSON with keys: relevant (boolean), niche_category (string),
score (integer 0-100), summary (string, max 60 words), reason (string).
Do not invent facts. If data is missing, say so in summary."""
    raw = _ask(prompt)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {"relevant": False, "niche_category": lead.get("niche",""),
                "score": 0, "summary": raw[:500], "reason": "Could not parse structured response."}

def generate_email(lead, campaign_brief, kind="initial", previous_email=""):
    prompt = f"""Write a concise, respectful {kind} business outreach email.
Sender brand: {SENDER_COMPANY}
Campaign: {campaign_brief}
Influencer public details: {json.dumps(lead, ensure_ascii=False)}
Previous email, if any: {previous_email}
Rules: don't invent compensation, product claims, or personal details; personalize only
using supplied profile facts; include a clear question/call-to-action; identify sender;
include a simple opt-out sentence. Return JSON only: subject, body."""
    raw = _ask(prompt, 700)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {"subject": f"Collaboration opportunity with {SENDER_COMPANY}", "body": raw}

def classify_reply(lead, email_body):
    prompt = f"""Classify this business email reply from an influencer.
Lead: {json.dumps(lead, ensure_ascii=False)}
Reply: {email_body}
Return ONLY JSON with classification (one of interested, not_interested, pricing,
collaboration_request, opt_out, other), summary, suggested_reply, next_action.
Do not send the reply. Draft only. Respect opt-outs."""
    raw = _ask(prompt, 900)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {"classification":"other","summary":raw[:300],"suggested_reply":"",
                "next_action":"Review manually"}
