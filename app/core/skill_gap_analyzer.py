import json
from collections import Counter
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY
from app.core.models import Job, Profile
from app.core.db import SessionLocal
from sqlalchemy import cast, Text, or_
from loguru import logger

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SKILL_EXTRACTION_PROMPT = """
You are analyzing job postings to identify the specific skills, technologies, tools, and certifications mentioned.

You will be given a batch of job descriptions. Extract a list of specific, named skills/technologies/tools/certifications mentioned across these postings. Focus on concrete, specific terms (e.g. "Kubernetes", "AWS Lambda", "Salesforce", "PMP certification") not vague categories (e.g. "cloud experience", "good communication").

Return a JSON object only. No explanation, no markdown, no code fences. Raw JSON only.

Return this structure:
{
  "skills": ["Skill Name 1", "Skill Name 2", ...]
}

Rules:
- Only include skills that are explicitly named in the text
- Normalize variations (e.g. "AWS" and "Amazon Web Services" should both become "AWS")
- Do not include generic soft skills like "communication" or "teamwork"
- Do not include the candidate's own profile skills, only extract from the job postings provided
- Return up to 40 distinct skills, ordered by how frequently they appear to be emphasized
"""

def get_recent_jobs(verdict_filter=None):
    db = SessionLocal()
    try:
        query = db.query(Job).filter(
            Job.triage_status == "complete",
            Job.description_cleaned.isnot(None)
        )
        if verdict_filter:
            conditions = [cast(Job.triage_result["verdict"], Text) == f'"{v}"' for v in verdict_filter]
            query = query.filter(or_(*conditions))
        return query.all()
    finally:
        db.close()

def extract_skills_from_batch(job_descriptions: list) -> list:
    combined_text = "\n\n---JOB POSTING---\n\n".join(job_descriptions[:15])
    combined_text = combined_text[:12000]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SKILL_EXTRACTION_PROMPT,
        messages=[
            {"role": "user", "content": f"Job postings:\n\n{combined_text}"}
        ]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
        return result.get("skills", [])
    except json.JSONDecodeError:
        logger.error(f"Failed to parse skill extraction response: {raw}")
        return []

def get_profile_skill_names(profile: Profile) -> set:
    names = set()
    for skill in (profile.skills or []):
        name = skill.get("name", "").lower().strip()
        if name:
            names.add(name)
            for word in name.replace("(", "").replace(")", "").split():
                if len(word) > 2:
                    names.add(word.lower())
    return names

def skill_in_profile(skill_name: str, profile_skill_names: set) -> bool:
    skill_lower = skill_name.lower().strip()
    if skill_lower in profile_skill_names:
        return True
    for profile_skill in profile_skill_names:
        if len(profile_skill) > 2 and (profile_skill in skill_lower or skill_lower in profile_skill):
            return True
    return False

def run_skill_gap_analysis(verdict_filter=None) -> dict:
    db = SessionLocal()
    try:
        profile = db.query(Profile).first()
        if not profile:
            return {"error": "No profile found"}

        jobs = get_recent_jobs(verdict_filter=verdict_filter)
        if not jobs:
            return {"error": "No triaged jobs found"}

        profile_skill_names = get_profile_skill_names(profile)

        descriptions = [j.description_cleaned for j in jobs if j.description_cleaned]
        all_extracted_skills = Counter()

        batch_size = 15
        for i in range(0, len(descriptions), batch_size):
            batch = descriptions[i:i + batch_size]
            skills = extract_skills_from_batch(batch)
            for skill in skills:
                all_extracted_skills[skill] += 1

        gaps = []
        covered = []

        for skill, count in all_extracted_skills.most_common(40):
            in_profile = skill_in_profile(skill, profile_skill_names)
            entry = {"skill": skill, "frequency": count, "total_jobs_analyzed": len(jobs)}
            if in_profile:
                covered.append(entry)
            else:
                gaps.append(entry)

        return {
            "total_jobs_analyzed": len(jobs),
            "gaps": gaps,
            "covered": covered
        }

    finally:
        db.close()