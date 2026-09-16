import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import cast, Text
from app.core.db import SessionLocal
from app.core.models import Job, Profile

db = SessionLocal()
profile = db.query(Profile).first()
preferred_locations = [l.lower() for l in (profile.location_preferences or [])]

jobs = db.query(Job).filter(
    Job.triage_status == "complete",
    cast(Job.triage_result["verdict"], Text) == '"Apply"',
    Job.is_dismissed == False
).all()

mismatches = []
for job in jobs:
    if job.remote_type == "onsite":
        location_lower = (job.location or "").lower()
        if not any(pref in location_lower for pref in preferred_locations):
            mismatches.append(job)

print(f"Total Apply jobs: {len(jobs)}")
print(f"Onsite jobs NOT in preferred locations: {len(mismatches)}")
print()
for job in mismatches:
    print(f"{job.title} | {job.company} | {job.location}")

db.close()