import json
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY
from app.core.models import Job, Profile
from app.core.triage_engine import build_profile_context

client = Anthropic(api_key=ANTHROPIC_API_KEY)

APPLICATION_SYSTEM_PROMPT = """
You are an expert technical resume writer and career strategist.

Your job is to generate tailored application content for a candidate applying to a specific job.

You will be given:
1. A candidate profile with skills, experience, and evidence of accomplishments
2. A job posting description
3. Positioning guidance from a prior analysis (what to emphasize, what to lead with)

Rules you must follow without exception:
- Every resume bullet must be traceable to specific evidence in the candidate profile. Never invent accomplishments.
- Use terminology and phrasing from the job description where it accurately reflects what the candidate did. This helps with ATS keyword matching, but only use terms that are truthfully applicable.
- Resume bullets should be quantified where the evidence supports it, and honest where it doesn't.
- Cover letter should be specific to this role and company, not generic. Reference something concrete from the job description.
- Generate a professional summary (3-4 sentences) that leads with the angle most relevant to THIS specific job, not the candidate's most prominent skill overall. Read the job description carefully and identify what the employer values most, then frame the candidate's identity around that. For example, if the job is about enterprise AI adoption, lead with AI depth and adoption experience, not instructional design. If the job is about database architecture, lead with Oracle/DBA depth. The summary should make the hiring manager feel this candidate was built for this role specifically.
- Generate a tailored skills section as 4-6 categories, each with a label and a comma-separated list of specific skills/tools. Reorder and select categories based on relevance to this job, leading with the most relevant. Only include skills present in the candidate's profile. Match the terminology style of the job description where truthful (e.g. if the JD says "Oracle RAC" and the candidate has Oracle Database evidence covering RAC, use "Oracle RAC" as a listed skill).
- Do not use cliche phrases like "results-driven", "team player", "passionate about", "proven track record".
- Keep cover letter to 3 paragraphs: opening hook tied to the role, relevant experience with evidence, closing call to action.
- LinkedIn outreach message should be brief (under 100 words), specific, and not generic networking language.

Return a JSON object only. No explanation, no markdown, no code fences. Raw JSON only.

Return exactly this structure:
{
  "professional_summary": "3-4 sentence professional summary tailored to this role",
  "skills_section": [
    {"category": "Category Name", "skills": "Skill A, Skill B, Skill C"},
    {"category": "Category Name", "skills": "Skill D, Skill E"}
  ],
  "resume_bullets": [
    "Bullet 1 text",
    "Bullet 2 text"
  ],
  "cover_letter": "Full cover letter text with paragraph breaks as \\n\\n",
  "email_subject": "Subject line text",
  "linkedin_outreach": "Outreach message text"
}
"""

def generate_application_package(job: Job, profile: Profile) -> dict:
    profile_context = build_profile_context(profile)

    positioning = (job.triage_result or {}).get("positioning", {})
    positioning_context = json.dumps(positioning, indent=2)

    user_message = f"""
CANDIDATE PROFILE:
{profile_context}

JOB POSTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}

Description:
{job.description_cleaned[:5000]}

POSITIONING GUIDANCE FROM PRIOR ANALYSIS:
{positioning_context}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=APPLICATION_SYSTEM_PROMPT,
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

    return json.loads(raw)