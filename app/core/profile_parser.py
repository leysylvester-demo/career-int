import json
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

PARSE_PROMPT = """
You are a professional resume parser for technical professionals.

Extract the following information from the resume text provided and return it as valid JSON only.
No explanation, no markdown, no code fences. Just the raw JSON object.

Return this exact structure:
{
  "full_name": "",
  "current_title": "",
  "target_titles": [],
  "years_experience": 0,
  "industries_target": [],
  "industries_avoid": [],
  "location_preferences": [],
  "remote_preference": "flexible",
  "compensation_floor": 0,
  "deal_breakers": [],
  "skills": [
    {
      "name": "",
      "category": "",
      "level": "expert | proficient | familiar",
      "years": 0,
      "evidence": []
    }
  ],
  "experience": [
    {
      "title": "",
      "company": "",
      "start": "",
      "end": "",
      "summary": "",
      "key_accomplishments": []
    }
  ],
  "certifications": [],
  "education": [
    {
      "degree": "",
      "field": "",
      "institution": "",
      "year": ""
    }
  ],
  "preferred_company_size": [],
  "preferred_domains": []
}

Rules:
- For each skill, populate the evidence array with specific accomplishments from the resume that demonstrate that skill
- Set level based on years and demonstrated depth: expert (7+ years with leadership), proficient (3-6 years), familiar (1-2 years)
- Extract all technical skills including databases, cloud platforms, programming languages, tools, and frameworks
- For experience entries, extract specific measurable accomplishments where possible
- If information is not present in the resume, use empty strings or empty arrays, never null
- years_experience should be total career years as an integer
- compensation_floor should be 0 if not mentioned
"""

def parse_resume(resume_text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=PARSE_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Parse this resume:\n\n{resume_text}"
            }
        ]
    )

    raw = response.content[0].text.strip()

    # Remove any markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw}")