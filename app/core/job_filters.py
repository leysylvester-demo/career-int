from datetime import datetime, timezone
from app.core.models import Job, Profile
from app.core.db import SessionLocal
from loguru import logger

def flag_low_quality_jobs():
    db = SessionLocal()
    try:
        from sqlalchemy import cast, String
        jobs = db.query(Job).filter(
            cast(Job.quality_flags, String).in_(["[]", "null"])
        ).all()
        flagged_count = 0

        for job in jobs:
            flags = []

            # Flag short descriptions
            if job.description_cleaned and len(job.description_cleaned) < 150:
                flags.append("description_too_short")

            # Flag old postings
            if job.posted_date:
                try:
                    posted = datetime.fromisoformat(
                        job.posted_date.replace("Z", "+00:00")
                    )
                    age_days = (datetime.now(timezone.utc) - posted).days
                    if age_days > 30:
                        flags.append("posting_too_old")
                except Exception:
                    pass

            # Flag missing apply link
            if not job.url:
                flags.append("no_apply_link")

            if flags:
                job.quality_flags = flags
                flagged_count += 1

        db.commit()
        logger.info(f"Quality check complete. {flagged_count} jobs flagged.")
        return flagged_count

    except Exception as e:
        db.rollback()
        logger.error(f"Error during quality flagging: {e}")
        return 0
    finally:
        db.close()

def location_matches_austin(job_location: str) -> bool:
    """
    Returns True if the job location is Austin, TX in any common format.
    """
    if not job_location:
        return False
    location_lower = job_location.lower()
    return "austin" in location_lower

def auto_skip_location_mismatches(profile_location_prefs, profile_deal_breakers):
    """
    Auto-skip jobs that are onsite, NOT remote, and NOT in Austin, TX,
    when the relocation deal breaker is present. Saves an API call
    for jobs that would be mechanically disqualified anyway.

    Rules:
    - Remote jobs: never skip
    - Onsite/hybrid in Austin: never skip
    - Onsite anywhere else: auto-skip (relocation deal breaker)
    """
    if not any("relocation" in db.lower() for db in (profile_deal_breakers or [])):
        return 0

    db = SessionLocal()
    skipped_count = 0
    try:
        pending_jobs = db.query(Job).filter(Job.triage_status == "pending").all()

        for job in pending_jobs:
            # Rule 1: Remote jobs are always fine, never auto-skip
            if job.remote_type == "remote":
                continue

            # Rule 2: Onsite/hybrid in Austin is fine, never auto-skip
            if location_matches_austin(job.location or ""):
                continue

            # Rule 3: Onsite, not remote, not Austin -> auto-skip
            if job.remote_type == "onsite":
                job.triage_status = "complete"
                job.triage_result = {
                    "verdict": "Skip",
                    "verdict_summary": f"Onsite role in {job.location}, outside Austin TX and not remote, conflicts with stated relocation deal breaker.",
                    "why_worth_attention": [],
                    "why_not_worth_attention": [
                        f"This role is onsite in {job.location}, which is not Austin, TX or remote",
                        "Requires full-time onsite relocation, which is a stated deal breaker"
                    ],
                    "concerns": ["Location and relocation requirements conflict with stated preferences"],
                    "missing_skills": [],
                    "recruiter_lens": {
                        "likely_strengths": [],
                        "likely_questions": [],
                        "rejection_risks": ["Location mismatch may be a factor in candidate's interest or availability"],
                        "standout_elements": []
                    },
                    "positioning": {
                        "experiences_to_emphasize": [],
                        "accomplishments_to_lead_with": [],
                        "most_relevant_strengths": [],
                        "experiences_to_de_emphasize": []
                    },
                    "why_not_me": {
                        "missing_required_skills": [],
                        "missing_certifications": [],
                        "experience_gaps": [],
                        "domain_gaps": [],
                        "leadership_gaps": [],
                        "technology_gaps": [],
                        "other_risks": [f"Location requires relocation to {job.location}, conflicting with stated preferences"]
                    }
                }
                skipped_count += 1

        db.commit()
        logger.info(f"Auto-skipped {skipped_count} jobs for location mismatch (no API call used).")
        return skipped_count

    except Exception as e:
        db.rollback()
        logger.error(f"Error during auto-skip: {e}")
        return 0
    finally:
        db.close()

