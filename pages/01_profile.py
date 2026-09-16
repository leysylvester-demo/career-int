import streamlit as st
import pdfplumber
import docx
import io
from app.core.profile_parser import parse_resume
from app.core.models import Profile
from app.core.db import SessionLocal

st.set_page_config(page_title="Profile Builder", layout="wide")
st.title("Professional Profile Builder")

def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def save_profile(data: dict, raw_text: str):
    db = SessionLocal()
    try:
        existing = db.query(Profile).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.raw_resume_text = raw_text
            db.commit()
            return "updated"
        else:
            profile = Profile(**data, raw_resume_text=raw_text)
            db.add(profile)
            db.commit()
            return "created"
    finally:
        db.close()

def load_profile():
    db = SessionLocal()
    try:
        return db.query(Profile).first()
    finally:
        db.close()

def empty_skill():
    return {"name": "", "category": "", "level": "proficient", "years": 0, "evidence": []}

def empty_experience():
    return {"title": "", "company": "", "start": "", "end": "", "summary": "", "key_accomplishments": []}

def empty_education():
    return {"degree": "", "field": "", "institution": "", "year": ""}

# ── Initialize session state from DB if not already loaded ──────
if "parsed_profile" not in st.session_state:
    existing = load_profile()
    if existing:
        st.session_state["parsed_profile"] = {
            "full_name": existing.full_name or "",
            "current_title": existing.current_title or "",
            "target_titles": existing.target_titles or [],
            "years_experience": existing.years_experience or 0,
            "industries_target": existing.industries_target or [],
            "industries_avoid": existing.industries_avoid or [],
            "location_preferences": existing.location_preferences or [],
            "remote_preference": existing.remote_preference or "flexible",
            "compensation_floor": existing.compensation_floor or 0,
            "deal_breakers": existing.deal_breakers or [],
            "skills": existing.skills or [],
            "experience": existing.experience or [],
            "certifications": existing.certifications or [],
            "education": existing.education or [],
            "preferred_company_size": existing.preferred_company_size or [],
            "preferred_domains": existing.preferred_domains or [],
        }
        st.session_state["raw_resume_text"] = existing.raw_resume_text or ""

# ── Step 1: Upload ──────────────────────────────────────────────
st.header("Step 1: Upload Your Resume")
st.caption("Upload to extract your profile automatically, or skip and fill in manually below.")

uploaded_file = st.file_uploader("Upload your resume (PDF or Word)", type=["pdf", "docx"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    if uploaded_file.name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    else:
        resume_text = extract_text_from_docx(file_bytes)

    st.success(f"Resume loaded. {len(resume_text)} characters extracted.")

    if st.button("Extract Profile with AI"):
        with st.spinner("Claude is analyzing your resume..."):
            try:
                parsed = parse_resume(resume_text)
                st.session_state["parsed_profile"] = parsed
                st.session_state["raw_resume_text"] = resume_text
                st.success("Profile extracted. Review and edit below.")
                st.rerun()
            except Exception as e:
                st.error(f"Extraction failed: {e}")

# ── Step 2: Review and Edit ─────────────────────────────────────
if "parsed_profile" in st.session_state:
    p = st.session_state["parsed_profile"]

    st.header("Step 2: Review and Edit Your Profile")
    st.info("Review every section. Add evidence to skills. Use the + buttons to add missing entries.")

    # Personal Information
    with st.expander("Personal Information", expanded=True):
        p["full_name"] = st.text_input("Full Name", value=p.get("full_name", ""))
        p["current_title"] = st.text_input("Current Title", value=p.get("current_title", ""))
        p["years_experience"] = st.number_input("Total Years of Experience", value=int(p.get("years_experience") or 0), min_value=0)
        p["remote_preference"] = st.selectbox(
            "Remote Preference",
            ["remote", "hybrid", "onsite", "flexible"],
            index=["remote", "hybrid", "onsite", "flexible"].index(p.get("remote_preference", "flexible"))
        )
        p["compensation_floor"] = st.number_input(
            "Minimum Acceptable Salary (USD)",
            value=int(p.get("compensation_floor") or 0),
            min_value=0,
            step=5000
        )

    # Target Roles
    with st.expander("Target Roles"):
        target_titles_raw = st.text_area(
            "Target Job Titles (one per line)",
            value="\n".join(p.get("target_titles", []))
        )
        p["target_titles"] = [t.strip() for t in target_titles_raw.split("\n") if t.strip()]

    # Location
    with st.expander("Location Preferences"):
        locations_raw = st.text_area(
            "Preferred Locations (one per line)",
            value="\n".join(p.get("location_preferences", []))
        )
        p["location_preferences"] = [l.strip() for l in locations_raw.split("\n") if l.strip()]

    # Industries
    with st.expander("Industries"):
        industries_target_raw = st.text_area(
            "Industries You Want (one per line)",
            value="\n".join(p.get("industries_target", []))
        )
        p["industries_target"] = [i.strip() for i in industries_target_raw.split("\n") if i.strip()]

        industries_avoid_raw = st.text_area(
            "Industries to Avoid (one per line)",
            value="\n".join(p.get("industries_avoid", []))
        )
        p["industries_avoid"] = [i.strip() for i in industries_avoid_raw.split("\n") if i.strip()]

    # Deal Breakers
    with st.expander("Deal Breakers"):
        deal_breakers_raw = st.text_area(
            "Deal Breakers (one per line)",
            value="\n".join(p.get("deal_breakers", []))
        )
        p["deal_breakers"] = [d.strip() for d in deal_breakers_raw.split("\n") if d.strip()]

    # Preferred Company Size
    with st.expander("Preferred Company Size"):
        company_size_raw = st.text_area(
            "Preferred Company Sizes (one per line)",
            value="\n".join(p.get("preferred_company_size", []))
        )
        p["preferred_company_size"] = [c.strip() for c in company_size_raw.split("\n") if c.strip()]

    # Preferred Domains
    with st.expander("Preferred Domains"):
        domains_raw = st.text_area(
            "Preferred Domains (one per line)",
            value="\n".join(p.get("preferred_domains", []))
        )
        p["preferred_domains"] = [d.strip() for d in domains_raw.split("\n") if d.strip()]

    # Skills
    with st.expander("Skills", expanded=True):
        st.caption("Add evidence for every skill. The triage engine uses this to make specific claims about your fit.")

        if "skills" not in p or p["skills"] is None:
            p["skills"] = []

        skills_to_delete = []

        for i, skill in enumerate(p["skills"]):
            st.markdown(f"**Skill {i+1}**")
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                skill["name"] = st.text_input("Skill Name", value=skill.get("name", ""), key=f"skill_name_{i}")
            with col2:
                skill["category"] = st.text_input("Category", value=skill.get("category", ""), key=f"skill_cat_{i}")
            with col3:
                skill["level"] = st.selectbox(
                    "Level",
                    ["expert", "proficient", "familiar"],
                    index=["expert", "proficient", "familiar"].index(skill.get("level", "proficient")),
                    key=f"skill_level_{i}"
                )
            with col4:
                skill["years"] = st.number_input("Years", value=int(skill.get("years") or 0), min_value=0, key=f"skill_years_{i}")

            evidence_raw = st.text_area(
                "Evidence (one per line)",
                value="\n".join(skill.get("evidence", [])),
                key=f"skill_evidence_{i}",
                help="List specific things you did that prove this skill"
            )
            skill["evidence"] = [e.strip() for e in evidence_raw.split("\n") if e.strip()]

            if st.button(f"Remove Skill {i+1}", key=f"remove_skill_{i}"):
                skills_to_delete.append(i)

            st.divider()

        for idx in sorted(skills_to_delete, reverse=True):
            p["skills"].pop(idx)

        if st.button("+ Add Skill"):
            p["skills"].append(empty_skill())
            st.rerun()

    # Work Experience
    with st.expander("Work Experience"):
        if "experience" not in p or p["experience"] is None:
            p["experience"] = []

        exp_to_delete = []

        for i, exp in enumerate(p["experience"]):
            st.markdown(f"**Position {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                exp["title"] = st.text_input("Title", value=exp.get("title", ""), key=f"exp_title_{i}")
                exp["start"] = st.text_input("Start Date", value=exp.get("start", ""), key=f"exp_start_{i}")
            with col2:
                exp["company"] = st.text_input("Company", value=exp.get("company", ""), key=f"exp_company_{i}")
                exp["end"] = st.text_input("End Date", value=exp.get("end", ""), key=f"exp_end_{i}")

            exp["summary"] = st.text_area("Summary", value=exp.get("summary", ""), key=f"exp_summary_{i}")
            accomplishments_raw = st.text_area(
                "Key Accomplishments (one per line)",
                value="\n".join(exp.get("key_accomplishments", [])),
                key=f"exp_accomplishments_{i}"
            )
            exp["key_accomplishments"] = [a.strip() for a in accomplishments_raw.split("\n") if a.strip()]

            if st.button(f"Remove Position {i+1}", key=f"remove_exp_{i}"):
                exp_to_delete.append(i)

            st.divider()

        for idx in sorted(exp_to_delete, reverse=True):
            p["experience"].pop(idx)

        if st.button("+ Add Position"):
            p["experience"].append(empty_experience())
            st.rerun()

    # Education
    with st.expander("Education"):
        if "education" not in p or p["education"] is None:
            p["education"] = []

        edu_to_delete = []

        for i, edu in enumerate(p["education"]):
            st.markdown(f"**Degree {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                edu["degree"] = st.text_input("Degree", value=edu.get("degree", ""), key=f"edu_degree_{i}")
                edu["institution"] = st.text_input("Institution", value=edu.get("institution", ""), key=f"edu_inst_{i}")
            with col2:
                edu["field"] = st.text_input("Field of Study", value=edu.get("field", ""), key=f"edu_field_{i}")
                edu["year"] = st.text_input("Year", value=str(edu.get("year", "")), key=f"edu_year_{i}")

            if st.button(f"Remove Degree {i+1}", key=f"remove_edu_{i}"):
                edu_to_delete.append(i)

            st.divider()

        for idx in sorted(edu_to_delete, reverse=True):
            p["education"].pop(idx)

        if st.button("+ Add Degree"):
            p["education"].append(empty_education())
            st.rerun()

    # Certifications
    with st.expander("Certifications"):
        certs_raw = st.text_area(
            "Certifications (one per line)",
            value="\n".join(p.get("certifications", []))
        )
        p["certifications"] = [c.strip() for c in certs_raw.split("\n") if c.strip()]

    # Step 3: Save
    st.header("Step 3: Save Your Profile")

    if st.button("Save Profile", type="primary"):
        try:
            result = save_profile(p, st.session_state.get("raw_resume_text", ""))
            st.success(f"Profile {result} successfully.")
        except Exception as e:
            st.error(f"Save failed: {e}")

# ── Saved Profile Summary ───────────────────────────────────────
st.divider()
st.header("Saved Profile Summary")

existing = load_profile()
if existing:
    st.success("A profile is saved in the database.")
    with st.expander("View saved profile"):
        st.json({
            "full_name": existing.full_name,
            "current_title": existing.current_title,
            "target_titles": existing.target_titles,
            "years_experience": existing.years_experience,
            "skills_count": len(existing.skills or []),
            "experience_count": len(existing.experience or []),
            "education_count": len(existing.education or []),
            "certifications": existing.certifications
        })
else:
    st.info("No profile saved yet. Upload your resume above to get started.")
