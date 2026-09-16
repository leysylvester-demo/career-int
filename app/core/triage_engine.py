import json
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY
from app.core.models import Job, Profile
from app.core.db import SessionLocal
from loguru import logger
from sqlalchemy import or_

client = Anthropic(api_key=ANTHROPIC_API_KEY)

TRIAGE_SYSTEM_PROMPT = """
You are a brutally honest career advisor for technical professionals.

Your job is to evaluate whether a job posting is worth a candidate's time and attention.

You will be given:
1. A candidate profile with skills, experience, and evidence of accomplishments
2. A job posting description

You must return a JSON object only. No explanation, no markdown, no code fences. Raw JSON only.

Rules you must follow without exception:
- Every positive claim must cite specific evidence from the candidate profile. Never say "strong background in X" without referencing what they actually did.
- Every verdict must include at least one concern, even on strong matches.
- The why_not_me section must be populated on every response, even Apply verdicts.
- Never be encouraging for its own sake. Honesty builds trust. Flattery wastes time.
- If the role is a poor match, say so clearly and explain why.
- If the candidate is overqualified, flag it. Overqualification causes rejection too.
- Location matters. If a job is onsite (not remote) and the location is NOT in the candidate's location preferences, this is a significant concern. If the candidate has no remote flexibility stated and the job requires onsite work in a location far from their preferences, the verdict should be Skip or Consider at best, not Apply, regardless of how well skills match.
- Recruiter lens must reflect how an external recruiter sees the candidate, not how the candidate sees themselves.

Return exactly this JSON structure:
{
  "verdict": "Apply | Consider | Skip",
  "verdict_summary": "One sentence explaining the verdict",
  "why_worth_attention": [],
  "why_not_worth_attention": [],
  "concerns": [],
  "missing_skills": [],
  "recruiter_lens": {
    "likely_strengths": [],
    "likely_questions": [],
    "rejection_risks": [],
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
    "other_risks": []
  }
}
"""

def build_profile_context(profile: Profile) -> str:
    lines = []
    lines.append(f"CANDIDATE: {profile.full_name}")
    lines.append(f"CURRENT TITLE: {profile.current_title}")
    lines.append(f"YEARS EXPERIENCE: {profile.years_experience}")
    lines.append(f"TARGET TITLES: {', '.join(profile.target_titles or [])}")
    lines.append(f"REMOTE PREFERENCE: {profile.remote_preference}")
    lines.append(f"COMPENSATION FLOOR: ${profile.compensation_floor:,}" if profile.compensation_floor else "COMPENSATION FLOOR: Not specified")
    lines.append(f"DEAL BREAKERS: {', '.join(profile.deal_breakers or [])}")
    lines.append(f"LOCATION PREFERENCES: {', '.join(profile.location_preferences or [])}")
    lines.append("")

    lines.append("SKILLS WITH EVIDENCE:")
    for skill in (profile.skills or []):
        lines.append(f"  Skill: {skill.get('name')} | Level: {skill.get('level')} | Years: {skill.get('years')}")
        for evidence in (skill.get('evidence') or []):
            lines.append(f"    - {evidence}")

    lines.append("")
    lines.append("WORK EXPERIENCE:")
    for exp in (profile.experience or []):
        lines.append(f"  {exp.get('title')} at {exp.get('company')} ({exp.get('start')} - {exp.get('end')})")
        lines.append(f"  Summary: {exp.get('summary')}")
        for accomplishment in (exp.get('key_accomplishments') or []):
            lines.append(f"    - {accomplishment}")

    lines.append("")
    lines.append("CERTIFICATIONS:")
    for cert in (profile.certifications or []):
        lines.append(f"  - {cert}")

    lines.append("")
    lines.append("EDUCATION:")
    for edu in (profile.education or []):
        lines.append(f"  - {edu.get('degree')} in {edu.get('field')}, {edu.get('institution')} ({edu.get('year')})")

    return "\n".join(lines)

def triage_job(job: Job, profile: Profile, retry: bool = True) -> dict:
    profile_context = build_profile_context(profile)

    user_message = f"""
CANDIDATE PROFILE:
{profile_context}

JOB POSTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Remote Type: {job.remote_type}

Description:
{job.description_cleaned[:3000]}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=TRIAGE_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        if retry:
            logger.warning(f"JSON parse failed for job {job.id}, retrying once: {e}")
            return triage_job(job, profile, retry=False)
        else:
            raise

def run_triage_batch(batch_size: int = 10) -> dict:
    db = SessionLocal()
    processed = 0
    failed = 0

    try:
        profile = db.query(Profile).first()
        if not profile:
            logger.error("No profile found. Build your profile first.")
            return {"processed": 0, "failed": 0, "error": "No profile found"}

        pending_jobs = (
            db.query(Job)
            .filter(or_(Job.triage_status == "pending", Job.triage_status == "failed"))
            .filter(Job.is_dismissed == False)
            .limit(batch_size)
            .all()
        )

        if not pending_jobs:
            logger.info("No pending jobs to triage.")
            return {"processed": 0, "failed": 0}

        logger.info(f"Triaging {len(pending_jobs)} jobs...")

        for job in pending_jobs:
            try:
                logger.info(f"Triaging: {job.title} at {job.company}")
                result = triage_job(job, profile)
                job.triage_result = result
                job.triage_status = "complete"
                db.commit()
                processed += 1
                logger.info(f"Verdict: {result.get('verdict')} - {result.get('verdict_summary')}")
            except Exception as e:
                logger.error(f"Failed to triage job {job.id}: {e}")
                job.triage_status = "failed"
                db.commit()
                failed += 1

        return {"processed": processed, "failed": failed}

    finally:
        db.close()