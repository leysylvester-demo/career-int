import streamlit as st
from datetime import datetime, date
from app.core.models import Job
from app.core.db import SessionLocal

st.set_page_config(page_title="Application Tracker", layout="wide")
st.title("Application Tracker")

PIPELINE_STATUSES = ["saved", "applied", "screened", "interviewed", "offer", "rejected", "accepted"]
STATUS_COLORS = {
    "saved": "⚪",
    "applied": "🔵",
    "screened": "🟣",
    "interviewed": "🟡",
    "offer": "🟢",
    "rejected": "🔴",
    "accepted": "✅"
}

def load_tracked_jobs(status_filter=None):
    db = SessionLocal()
    try:
        query = db.query(Job).filter(Job.pipeline_status != "none")
        if status_filter and status_filter != "All":
            query = query.filter(Job.pipeline_status == status_filter)
        return query.order_by(Job.applied_date.desc().nullslast(), Job.collected_at.desc()).all()
    finally:
        db.close()

def get_pipeline_counts():
    db = SessionLocal()
    try:
        counts = {}
        for status in PIPELINE_STATUSES:
            counts[status] = db.query(Job).filter(Job.pipeline_status == status).count()
        return counts
    finally:
        db.close()

def update_job(job_id, status=None, notes=None, next_action=None, next_action_date=None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            if status is not None:
                job.pipeline_status = status
                if status == "applied" and job.applied_date is None:
                    job.applied_date = datetime.utcnow()
                if status == "applied":
                    job.is_applied = True
            if notes is not None:
                job.notes = notes
            if next_action is not None:
                job.next_action = next_action
            if next_action_date is not None:
                job.next_action_date = next_action_date
            db.commit()
    finally:
        db.close()

# ── Pipeline Overview ────────────────────────────────────────────
counts = get_pipeline_counts()
cols = st.columns(len(PIPELINE_STATUSES))
for i, status in enumerate(PIPELINE_STATUSES):
    cols[i].metric(f"{STATUS_COLORS[status]} {status.capitalize()}", counts[status])

st.divider()

# ── Filter ────────────────────────────────────────────────────────
status_filter = st.selectbox("Filter by status", ["All"] + PIPELINE_STATUSES)
jobs = load_tracked_jobs(status_filter)

st.markdown(f"Showing **{len(jobs)}** tracked applications")
st.divider()

# ── Job Cards ─────────────────────────────────────────────────────
if not jobs:
    st.info("No applications tracked yet. Go to the Dashboard and click 'Save' or 'Mark Applied' on jobs you want to track.")
else:
    for job in jobs:
        status_icon = STATUS_COLORS.get(job.pipeline_status, "⚪")

        with st.expander(f"{status_icon} {job.title} — {job.company} | Status: {job.pipeline_status.upper()}"):

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Location:** {job.location}")
                st.markdown(f"**Remote:** {job.remote_type}")
                if job.applied_date:
                    st.markdown(f"**Applied:** {job.applied_date.strftime('%Y-%m-%d')}")
                if job.url:
                    st.markdown(f"[View Job Posting]({job.url})")
            with col2:
                if job.triage_result:
                    verdict = job.triage_result.get("verdict", "")
                    st.markdown(f"**Original Verdict:** {verdict}")

            st.divider()

            # Status update
            new_status = st.selectbox(
                "Pipeline Status",
                PIPELINE_STATUSES,
                index=PIPELINE_STATUSES.index(job.pipeline_status) if job.pipeline_status in PIPELINE_STATUSES else 0,
                key=f"status_{job.id}"
            )

            # Notes
            notes = st.text_area(
                "Notes (interview prep, contacts, feedback received, etc.)",
                value=job.notes or "",
                key=f"notes_{job.id}"
            )

            # Next action
            col1, col2 = st.columns(2)
            with col1:
                next_action = st.text_input(
                    "Next Action",
                    value=job.next_action or "",
                    key=f"next_action_{job.id}"
                )
            with col2:
                next_action_date = st.date_input(
                    "Next Action Date",
                    value=job.next_action_date.date() if job.next_action_date else date.today(),
                    key=f"next_date_{job.id}"
                )

            if st.button("Update", key=f"update_{job.id}"):
                update_job(
                    job.id,
                    status=new_status,
                    notes=notes,
                    next_action=next_action,
                    next_action_date=datetime.combine(next_action_date, datetime.min.time())
                )
                st.success("Updated.")
                st.rerun()

# ── Upcoming Actions ──────────────────────────────────────────────
st.divider()
st.header("Upcoming Actions")

db = SessionLocal()
try:
    upcoming = db.query(Job).filter(
        Job.next_action != "",
        Job.next_action.isnot(None),
        Job.pipeline_status.notin_(["rejected", "accepted"])
    ).order_by(Job.next_action_date.asc()).all()
finally:
    db.close()

if not upcoming:
    st.info("No upcoming actions scheduled.")
else:
    for job in upcoming:
        date_str = job.next_action_date.strftime("%Y-%m-%d") if job.next_action_date else "No date"
        st.markdown(f"**{date_str}** — {job.next_action} — *{job.title} at {job.company}*")