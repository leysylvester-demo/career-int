import streamlit as st
from app.core.models import Job
from app.core.db import SessionLocal
from sqlalchemy import cast, Text, func

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Career Intelligence Dashboard")

def load_jobs_by_verdict(verdict=None, keyword=None, remote_only=False):
    db = SessionLocal()
    try:
        query = db.query(Job).filter(
            Job.triage_status == "complete",
            Job.is_dismissed == False,
            Job.pipeline_status == "none"
        )
        if verdict:
            query = query.filter(cast(Job.triage_result["verdict"], Text) == f'"{verdict}"')
        if remote_only:
            query = query.filter(Job.remote_type == "remote")
        if keyword:
            query = query.filter(
                Job.title.ilike(f"%{keyword}%") |
                Job.company.ilike(f"%{keyword}%")
            )
        return query.order_by(Job.collected_at.desc()).all()
    finally:
        db.close()

def get_verdict_counts():
    db = SessionLocal()
    try:
        apply = db.query(Job).filter(
            Job.triage_status == "complete",
            cast(Job.triage_result["verdict"], Text) == '"Apply"',
            Job.is_dismissed == False,
            Job.pipeline_status == "none"
        ).count()
        consider = db.query(Job).filter(
            Job.triage_status == "complete",
            cast(Job.triage_result["verdict"], Text) == '"Consider"',
            Job.is_dismissed == False,
            Job.pipeline_status == "none"
        ).count()
        skip = db.query(Job).filter(
            Job.triage_status == "complete",
            cast(Job.triage_result["verdict"], Text) == '"Skip"',
            Job.is_dismissed == False,
            Job.pipeline_status == "none"
        ).count()
        applied = db.query(Job).filter(Job.is_applied == True).count()
        return {"apply": apply, "consider": consider, "skip": skip, "applied": applied}
    finally:
        db.close()

def mark_applied(job_id: int):
    from datetime import datetime
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_applied = True
            job.pipeline_status = "applied"
            job.applied_date = datetime.utcnow()
            db.commit()
    finally:
        db.close()

def mark_dismissed(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_dismissed = True
            db.commit()
    finally:
        db.close()

def mark_saved(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_saved = True
            if job.pipeline_status == "none":
                job.pipeline_status = "saved"
            db.commit()
    finally:
        db.close()

# ── Stats Bar ───────────────────────────────────────────────────
counts = get_verdict_counts()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Apply", counts["apply"])
col2.metric("Consider", counts["consider"])
col3.metric("Skip", counts["skip"])
col4.metric("Applied", counts["applied"])

st.divider()

# ── Filters ─────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    verdict_filter = st.selectbox(
        "Verdict",
        ["All", "Apply", "Consider", "Skip"],
        index=1
    )
with col2:
    keyword = st.text_input("Search title or company")
with col3:
    remote_only = st.checkbox("Remote only")

verdict_param = None if verdict_filter == "All" else verdict_filter
jobs = load_jobs_by_verdict(verdict=verdict_param, keyword=keyword, remote_only=remote_only)

st.markdown(f"Showing **{len(jobs)}** jobs")
st.divider()

# ── Job Cards ───────────────────────────────────────────────────
if not jobs:
    st.info("No jobs found for this filter.")
else:
    for job in jobs:
        result = job.triage_result or {}
        verdict = result.get("verdict", "Unknown")
        summary = result.get("verdict_summary", "")

        if verdict == "Apply":
            verdict_color = "🟢"
        elif verdict == "Consider":
            verdict_color = "🟡"
        else:
            verdict_color = "🔴"

        with st.expander(f"{verdict_color} {job.title} — {job.company} | {job.location}"):

            # Header row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Verdict:** {verdict}")
                st.markdown(f"**Posted:** {job.posted_date[:10] if job.posted_date else 'Unknown'}")
            with col2:
                st.markdown(f"**Remote:** {job.remote_type}")
                if job.salary_min and job.salary_max:
                    st.markdown(f"**Salary:** ${job.salary_min:,} - ${job.salary_max:,}")
            with col3:
                if job.url:
                    st.markdown(f"[View Job Posting]({job.url})")

            st.markdown(f"**Summary:** {summary}")
            st.divider()

            # Triage details
            tab1, tab2, tab3, tab4 = st.tabs(["Fit Analysis", "Recruiter Lens", "Positioning", "Why Not Me"])

            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Why Worth Attention**")
                    for item in result.get("why_worth_attention", []):
                        st.markdown(f"- {item}")
                with col2:
                    st.markdown("**Concerns**")
                    for item in result.get("concerns", []):
                        st.markdown(f"- {item}")

                if result.get("missing_skills"):
                    st.markdown("**Missing Skills**")
                    for item in result.get("missing_skills", []):
                        st.markdown(f"- {item}")

            with tab2:
                recruiter = result.get("recruiter_lens", {})
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Likely Strengths**")
                    for item in recruiter.get("likely_strengths", []):
                        st.markdown(f"- {item}")
                    st.markdown("**Standout Elements**")
                    for item in recruiter.get("standout_elements", []):
                        st.markdown(f"- {item}")
                with col2:
                    st.markdown("**Likely Questions**")
                    for item in recruiter.get("likely_questions", []):
                        st.markdown(f"- {item}")
                    st.markdown("**Rejection Risks**")
                    for item in recruiter.get("rejection_risks", []):
                        st.markdown(f"- {item}")

            with tab3:
                positioning = result.get("positioning", {})
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Experiences to Emphasize**")
                    for item in positioning.get("experiences_to_emphasize", []):
                        st.markdown(f"- {item}")
                    st.markdown("**Accomplishments to Lead With**")
                    for item in positioning.get("accomplishments_to_lead_with", []):
                        st.markdown(f"- {item}")
                with col2:
                    st.markdown("**Most Relevant Strengths**")
                    for item in positioning.get("most_relevant_strengths", []):
                        st.markdown(f"- {item}")
                    st.markdown("**De-emphasize**")
                    for item in positioning.get("experiences_to_de_emphasize", []):
                        st.markdown(f"- {item}")

            with tab4:
                why_not = result.get("why_not_me", {})
                col1, col2 = st.columns(2)
                with col1:
                    if why_not.get("missing_required_skills"):
                        st.markdown("**Missing Required Skills**")
                        for item in why_not.get("missing_required_skills", []):
                            st.markdown(f"- {item}")
                    if why_not.get("experience_gaps"):
                        st.markdown("**Experience Gaps**")
                        for item in why_not.get("experience_gaps", []):
                            st.markdown(f"- {item}")
                    if why_not.get("technology_gaps"):
                        st.markdown("**Technology Gaps**")
                        for item in why_not.get("technology_gaps", []):
                            st.markdown(f"- {item}")
                with col2:
                    if why_not.get("leadership_gaps"):
                        st.markdown("**Leadership Gaps**")
                        for item in why_not.get("leadership_gaps", []):
                            st.markdown(f"- {item}")
                    if why_not.get("domain_gaps"):
                        st.markdown("**Domain Gaps**")
                        for item in why_not.get("domain_gaps", []):
                            st.markdown(f"- {item}")
                    if why_not.get("other_risks"):
                        st.markdown("**Other Risks**")
                        for item in why_not.get("other_risks", []):
                            st.markdown(f"- {item}")

            st.divider()

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Mark Applied", key=f"apply_{job.id}"):
                    mark_applied(job.id)
                    st.success("Marked as applied.")
                    st.rerun()
            with col2:
                if st.button("Save", key=f"save_{job.id}"):
                    mark_saved(job.id)
                    st.success("Saved.")
                    st.rerun()
            with col3:
                if st.button("Dismiss", key=f"dismiss_{job.id}"):
                    mark_dismissed(job.id)
                    st.success("Dismissed.")
                    st.rerun()