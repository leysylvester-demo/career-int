import streamlit as st
from app.core.models import Job
from app.core.db import SessionLocal

st.set_page_config(page_title="Job Feed", layout="wide")
st.title("Job Feed")

def load_jobs(filter_status=None, remote_only=False, keyword=None):
    db = SessionLocal()
    try:
        query = db.query(Job).filter(Job.is_dismissed == False)
        if remote_only:
            query = query.filter(Job.remote_type == "remote")
        if keyword:
            query = query.filter(
                Job.title.ilike(f"%{keyword}%") |
                Job.company.ilike(f"%{keyword}%")
            )
        return query.order_by(Job.collected_at.desc()).limit(200).all()
    finally:
        db.close()

def get_stats():
    db = SessionLocal()
    try:
        total = db.query(Job).count()
        pending = db.query(Job).filter(Job.triage_status == "pending").count()
        from sqlalchemy import cast, Text
        flagged = db.query(Job).filter(
            cast(Job.quality_flags, Text) != '[]'
        ).count()
        return {"total": total, "pending": pending, "flagged": flagged}
    finally:
        db.close()

def db_session_pending_count():
    db = SessionLocal()
    try:
        return db.query(Job).filter(Job.triage_status == "pending").count()
    finally:
        db.close()

# Stats bar
stats = get_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Total Jobs Collected", stats["total"])
col2.metric("Pending Triage", stats["pending"])
col3.metric("Quality Flagged", stats["flagged"])

st.divider()

# Filters
st.subheader("Filters")
col1, col2, col3 = st.columns(3)
with col1:
    keyword = st.text_input("Search by title or company")
with col2:
    remote_only = st.checkbox("Remote only")
with col3:
    if st.button("Run Job Collection Now"):
        with st.spinner("Collecting jobs..."):
            try:
                import subprocess
                import sys
                subprocess.run([sys.executable, "scripts/collect_jobs.py"], check=True)
                st.success("Collection complete. Refresh the page to see new jobs.")
            except Exception as e:
                st.error(f"Collection failed: {e}")

st.divider()

# Triage section
# Triage section
pending_count = db_session_pending_count()

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**{pending_count}** jobs pending triage.")
with col2:
    if st.button("Run Triage Now (10 jobs)", disabled=(pending_count == 0)):
        with st.spinner("Triaging up to 10 jobs..."):
            try:
                import subprocess
                import sys
                subprocess.run([sys.executable, "scripts/run_triage.py"], check=True)
                st.success("Triage complete. Refresh to see updated verdicts.")
            except Exception as e:
                st.error(f"Triage failed: {e}")
                
# Job list
jobs = load_jobs(remote_only=remote_only, keyword=keyword)

if not jobs:
    st.info("No jobs found. Run a collection to get started.")
else:
    st.markdown(f"Showing **{len(jobs)}** jobs")

    for job in jobs:
        flags = job.quality_flags or []
        flag_label = "⚠️ " if flags else ""

        with st.expander(f"{flag_label}{job.title} — {job.company} | {job.location} | {job.triage_status.upper()}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Posted:** {job.posted_date[:10] if job.posted_date else 'Unknown'}")
                st.markdown(f"**Remote:** {job.remote_type}")
                st.markdown(f"**Source:** {job.source}")
            with col2:
                if job.salary_min or job.salary_max:
                    st.markdown(f"**Salary:** ${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min and job.salary_max else "**Salary:** Not listed")
                if flags:
                    st.markdown(f"**Flags:** {', '.join(flags)}")
                if job.url:
                    st.markdown(f"[View Job Posting]({job.url})")

            if job.description_cleaned:
                st.markdown("**Description:**")
                st.text(job.description_cleaned[:800] + "..." if len(job.description_cleaned) > 800 else job.description_cleaned)