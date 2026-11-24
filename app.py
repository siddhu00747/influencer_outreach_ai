import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from database import init_db, all_leads, get_lead, upsert_lead, update_lead, get_replies
from claude_agent import analyze_influencer, generate_email
from google_services import append_lead_to_sheet
from workflow import approve_and_send, process_replies, due_followups, send_followup
from config import SENDER_COMPANY

st.set_page_config(page_title="AI Influencer Outreach", page_icon="✉️", layout="wide")
init_db()

st.title("🤝 AI Influencer Outreach Assistant")
st.caption("Research • Claude AI qualification • CRM • Gmail outreach • Follow-ups • Reply intelligence")

with st.sidebar:
    st.header("Campaign")
    campaign = st.text_area("Campaign brief", value=f"{SENDER_COMPANY} is looking for relevant creators for a brand collaboration. Explain the product, target audience, deliverables and geography here.", height=150)
    st.info("Use only public business contact details and authorized profile data. Review every message before sending.")

leads = all_leads()
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total leads",len(leads))
c2.metric("Qualified",sum(1 for x in leads if x.get("score",0)>=70))
c3.metric("Emails sent",sum(1 for x in leads if x.get("last_sent_at")))
c4.metric("Interested",sum(1 for x in leads if x.get("status")=="Interested"))

tab1,tab2,tab3,tab4,tab5 = st.tabs(["Import & Research","Lead CRM","Email Approval","Replies","Follow-ups"])

with tab1:
    st.subheader("Import influencer records")
    st.write("Upload CSV with columns: name, username, profile_url, niche, followers, email, location.")
    sample = pd.DataFrame([{"name":"Demo Creator","username":"demo_creator","profile_url":"https://www.instagram.com/demo_creator/","niche":"Skincare","followers":25000,"email":"creator@example.com","location":"Delhi"}])
    st.download_button("Download sample CSV",sample.to_csv(index=False), "sample_influencers.csv","text/csv")
    uploaded = st.file_uploader("Upload CSV",type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded).fillna("")
        st.dataframe(df, use_container_width=True)
        if st.button("Import leads",type="primary"):
            count=0
            for row in df.to_dict("records"):
                try:
                    upsert_lead(row); count+=1
                except Exception as e: st.error(str(e))
            st.success(f"Imported/updated {count} records.")
            st.rerun()
    st.divider()
    st.subheader("Run Claude qualification")
    candidates=[x for x in all_leads() if x.get("email") or x.get("username")]
    if candidates:
        selected=st.selectbox("Choose a lead",candidates,format_func=lambda x:f"{x['name']} (@{x['username']})")
        if st.button("Analyze with Claude"):
            with st.spinner("Claude is reviewing the supplied profile data..."):
                result=analyze_influencer(selected,campaign)
            update_lead(selected["id"],score=result.get("score",0),summary=result.get("summary",""))
            st.json(result)
            st.success("Analysis saved.")
        if st.button("Sync selected lead to Google Sheets"):
            st.success(append_lead_to_sheet(selected))
    else: st.info("Import a CSV to begin.")

with tab2:
    st.subheader("CRM")
    data=all_leads()
    if data:
        view=pd.DataFrame(data)
        cols=[c for c in ["id","name","username","niche","followers","email","location","score","status","followup_count"] if c in view]
        st.dataframe(view[cols],use_container_width=True,hide_index=True)
        lead_id=st.selectbox("Update lead status", [x["id"] for x in data], format_func=lambda i: f"#{i} — {next(x['name'] for x in data if x['id']==i)}")
        status=st.selectbox("Status",["New Lead","Email Available","Email Sent","Follow-up Due","Replied","Interested","Not Interested","Collaboration Confirmed"])
        if st.button("Save status"): update_lead(lead_id,status=status); st.success("Updated"); st.rerun()
    else: st.info("No leads yet.")

with tab3:
    st.subheader("AI-generated email drafts — human approval required")
    eligible=[x for x in all_leads() if x.get("email") and not x.get("opt_out")]
    if eligible:
        lead=st.selectbox("Select recipient",eligible,key="email_lead",format_func=lambda x:f"{x['name']} <{x['email']}>")
        if st.button("Generate personalized email"):
            with st.spinner("Generating with Claude..."):
                draft=generate_email(lead,campaign)
            st.session_state["draft_subject"]=draft["subject"]
            st.session_state["draft_body"]=draft["body"]
            st.session_state["draft_lead_id"]=lead["id"]
        if "draft_subject" in st.session_state and st.session_state.get("draft_lead_id")==lead["id"]:
            subject=st.text_input("Subject",key="draft_subject")
            body=st.text_area("Email body",key="draft_body",height=250)
            st.warning("Review recipient, facts, wording and opt-out language before sending.")
            confirm=st.checkbox(f"I approve sending this email to {lead['email']}.")
            if st.button("Approve & send via Gmail",type="primary",disabled=not confirm):
                try:
                    result=approve_and_send(lead["id"],subject,body)
                    st.success(f"Sent. Gmail message ID: {result.get('id')}")
                    st.session_state.pop("draft_subject",None); st.session_state.pop("draft_body",None)
                    st.rerun()
                except Exception as e: st.error(str(e))
    else: st.info("Add a lead with a public business email first.")

with tab4:
    st.subheader("Incoming replies")
    if st.button("Check Gmail inbox for replies"):
        with st.spinner("Reading recent inbox messages and classifying matched leads..."):
            try:
                result=process_replies()
                st.success(f"Processed {len(result)} matching replies.")
                if result: st.dataframe(pd.DataFrame(result),use_container_width=True)
            except Exception as e: st.error(str(e))
    replies=get_replies()
    if replies:
        for r in replies:
            with st.expander(f"{r['name']} — {r['classification']} — {r['received_at']}"):
                st.write("**Original reply**"); st.write(r["body"])
                st.write("**AI suggested reply (draft only)**")
                draft=st.text_area("Review/edit reply",value=r["suggested_reply"],key=f"reply_{r['id']}",height=140)
                st.caption("This starter version stores AI reply drafts for human review. Sending a reply can be added after confirming the correct Gmail thread and recipient.")
    else: st.info("No matched replies processed yet.")

with tab5:
    st.subheader("Follow-up queue")
    due=due_followups()
    if due: st.dataframe(pd.DataFrame(due),use_container_width=True,hide_index=True)
    else: st.success("No follow-ups currently due.")
    follow_leads=[x for x in all_leads() if x["status"] in ("Email Sent","Follow-up Due") and not x["opt_out"] and int(x["followup_count"] or 0)<2]
    if follow_leads:
        lead=st.selectbox("Select lead for follow-up",follow_leads,key="follow_lead",format_func=lambda x:f"{x['name']} — follow-ups sent: {x['followup_count']}")
        if st.button("Generate follow-up draft"):
            draft=generate_email(lead,campaign,kind="follow-up",previous_email=lead.get("initial_body",""))
            st.session_state["fu_subject"]=draft["subject"]; st.session_state["fu_body"]=draft["body"]; st.session_state["fu_id"]=lead["id"]
        if st.session_state.get("fu_id")==lead["id"]:
            sub=st.text_input("Follow-up subject",key="fu_subject")
            bod=st.text_area("Follow-up body",key="fu_body",height=180)
            ok=st.checkbox(f"Approve follow-up to {lead['email']}",key="fu_ok")
            if st.button("Approve & send follow-up",disabled=not ok):
                try:
                    # Use edited draft; send only after explicit approval.
                    from google_services import send_email
                    from datetime import datetime, timezone
                    result=send_email(lead["email"],sub,bod,lead.get("last_gmail_thread_id"))
                    update_lead(lead["id"],status="Follow-up Due",last_sent_at=datetime.now(timezone.utc).isoformat(),
                                followup_count=int(lead["followup_count"] or 0)+1,last_gmail_thread_id=result.get("threadId"))
                    st.success("Follow-up sent."); st.rerun()
                except Exception as e: st.error(str(e))
    st.caption("Scheduling policy: first follow-up after 3–5 days; second after another 5–7 days. Replies, declines and opt-outs must stop outreach. This dashboard exposes due items; review and approve before sending.")
