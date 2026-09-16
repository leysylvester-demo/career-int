import streamlit as st
from app.core.models import Job, Profile
from app.core.db import SessionLocal
from app.core.application_generator import generate_application_package

st.set_page_config(page_title="Application Assistant", layout="wide")
st.title("Application Assistant")

def load_apply_jobs():
    db = SessionLocal()
    try:
        return db.query(Job).filter(
            Job.triage_status == "complete",
            Job.is_dismissed == False
        ).order_by(Job.collected_at.desc()).all()
    finally:
        db.close()

def get_profile():
    db = SessionLocal()
    try:
        return db.query(Profile).first()
    finally:
        db.close()

def save_package(job_id, package):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.application_package = package
            db.commit()
    finally:
        db.close()

st.caption("Generate tailored resume bullets, cover letters, and outreach messages for your Apply and Consider tier jobs.")
if "current_package_job_id" not in st.session_state:
    st.session_state["current_package_job_id"] = None
    
jobs = load_apply_jobs()
profile = get_profile()

if not profile:
    st.error("No profile found. Build your profile first.")
    st.stop()

if not jobs:
    st.info("No Apply or Consider jobs found. Run triage first.")
    st.stop()

col1, col2 = st.columns([1, 3])
with col1:
    verdict_filter = st.selectbox("Filter by verdict", ["All", "Apply", "Consider", "Skip"])

if verdict_filter != "All":
    jobs = [j for j in jobs if (j.triage_result or {}).get("verdict") == verdict_filter]

if not jobs:
    st.info(f"No jobs with verdict '{verdict_filter}'.")
    st.stop()

job_options = {}
for job in jobs:
    verdict = (job.triage_result or {}).get("verdict", "?")
    label = f"[{verdict}] {job.title} — {job.company}"
    job_options[label] = job

with col2:
    selected_label = st.selectbox("Select a job", list(job_options.keys()))
selected_job = job_options[selected_label]
if st.session_state.get("current_package_job_id") != selected_job.id:
    st.session_state.pop("current_package", None)
    st.session_state["current_package_job_id"] = selected_job.id

verdict = (selected_job.triage_result or {}).get("verdict", "")
st.markdown(f"**Verdict:** {verdict}")
if selected_job.url:
    st.markdown(f"[View Job Posting]({selected_job.url})")

st.divider()

if selected_job.application_package:
    st.success("Application package already generated. Edit below or regenerate.")

if st.button("Generate Application Package", type="primary"):
    with st.spinner("Generating tailored content..."):
        try:
            package = generate_application_package(selected_job, profile)
            save_package(selected_job.id, package)
            st.session_state["current_package"] = package
            st.success("Generated successfully.")
        except Exception as e:
            st.error(f"Generation failed: {e}")

# Display package
package = st.session_state.get("current_package") or selected_job.application_package

if package:
    st.divider()

    st.header("Professional Summary")
    st.caption("Tailored framing for the top of your resume for this role.")
    st.text_area("Summary", value=package.get("professional_summary", ""), height=120, key="summary_display")

    st.header("Skills Section")
    st.caption("Reordered and curated based on relevance to this role.")
    skills_lines = []
    for cat in package.get("skills_section", []):
        skills_lines.append(f"{cat.get('category', '')}: {cat.get('skills', '')}")
    skills_text = "\n".join(skills_lines)
    st.text_area("Skills", value=skills_text, height=150, key="skills_display")

    st.header("Resume Bullets")
    st.caption("Copy these into your resume's experience section for this application.")
    bullets_text = "\n".join([f"- {b}" for b in package.get("resume_bullets", [])])
    st.text_area("Bullets", value=bullets_text, height=200, key="bullets_display")

    st.header("Cover Letter")
    cover_letter = package.get("cover_letter", "").replace("\\n\\n", "\n\n")
    st.text_area("Cover Letter", value=cover_letter, height=300, key="cover_display")

    st.header("Email Subject Line")
    st.text_input("Subject", value=package.get("email_subject", ""), key="subject_display")

    st.header("LinkedIn Outreach Message")
    st.text_area("Outreach", value=package.get("linkedin_outreach", ""), height=120, key="outreach_display")