"""Optional scheduler process. Run with: python worker.py
It reports due follow-ups; it deliberately does not auto-send without human approval."""
from apscheduler.schedulers.blocking import BlockingScheduler
from workflow import due_followups

def check_queue():
    due = due_followups()
    if due:
        print("FOLLOW-UPS NEED HUMAN REVIEW:")
        for item in due: print(item)
    else:
        print("No follow-ups due.")

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(check_queue, "interval", hours=6, id="followup_queue")
    check_queue()
    scheduler.start()
