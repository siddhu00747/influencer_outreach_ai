# AI Influencer Outreach Assistant

A practical internship-assignment implementation: public/authorized influencer data import, Claude qualification, SQLite CRM, optional Google Sheets sync, Gmail outreach with explicit approval, inbox reply classification and follow-up queue.

## Important scope and safety
- Instagram discovery is intentionally based on CSV/manual research or an authorized API/export. This project does **not** bypass login, scrape private profiles, evade rate limits, or harvest private contact data.
- Only use publicly listed business contact details and test records where you have permission.
- Initial emails, follow-ups and AI reply drafts require human review/approval. The starter app does not auto-send AI-generated replies.
- The follow-up queue is surfaced for review; it does not silently send messages.
- Respect opt-outs immediately. Do not contact people who opted out.

## 1. Setup
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; use cp on macOS/Linux
```

Edit `.env`:
- `ANTHROPIC_API_KEY`: your Anthropic API key.
- `CLAUDE_MODEL`: a model available to your Anthropic account.
- `SENDER_NAME`, `SENDER_COMPANY`: sender details.
- `GOOGLE_SHEET_ID`: optional spreadsheet ID. Create a tab named `Leads` with headers in columns A:I.

## 2. Google OAuth setup
1. Open Google Cloud Console and create/select a project.
2. Enable **Gmail API** and **Google Sheets API**.
3. Configure OAuth consent screen. For personal testing, add your Google account as a test user if the app is in Testing.
4. Create OAuth Client ID → Desktop app.
5. Download the JSON and save it beside `app.py` as `credentials.json`.
6. First Gmail/Sheets action opens a browser for consent and creates `token.json`.
7. Keep `credentials.json` and `token.json` private. Never commit them.

Scopes requested: Gmail modify/send and Sheets access. Use a dedicated test account during development.

## 3. Run
```bash
streamlit run app.py
```

## 4. Test workflow
1. Download the sample CSV from the dashboard or prepare your own CSV.
2. Import test/public influencer records.
3. Add campaign details in the sidebar.
4. Run Claude qualification.
5. Optionally sync a lead to the Google Sheet.
6. Generate a personalized email and inspect it.
7. Tick the approval checkbox and send to a test inbox first.
8. Reply to that test email from another account.
9. Use **Check Gmail inbox for replies**. Matched replies are classified and saved as drafts.
10. Review follow-up queue. Generate and approve follow-up manually.

Use `creator@example.com` only as a placeholder; replace it with an address you control for end-to-end tests.

## 5. Data model
`outreach.db` is created automatically. `leads` stores profile data, score, status, send timestamps, follow-up count and opt-out flag. `replies` stores matched inbound messages and AI draft suggestions.

## 6. Submission demo checklist
- Show CSV import and duplicate username handling.
- Show Claude relevance score and summary.
- Show CRM and Google Sheets sync.
- Show generated email before approval, then send to a test inbox.
- Reply from a second mailbox and show classification + reply draft.
- Show follow-up due queue and approval-based sending.
- Explain that Instagram data collection uses authorized/public sources.

## Current implementation notes
This is a working starter implementation, not a fully unattended production campaign system. The reply monitor matches senders by email address and scans recent inbox messages; for production, add robust thread/message deduplication, MIME parsing for HTML-only messages, pagination, sender authentication, bounce handling and Google Sheets update/upsert logic. Follow-up due calculation is exposed in the dashboard and optional worker; sending remains human-approved.
