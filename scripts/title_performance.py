import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from sqlalchemy import cast, Text
from app.core.db import SessionLocal
from app.core.models import Job, Profile

db = SessionLocal()
profile = db.query(Profile).first()
target_titles = profile.target_titles or []

jobs = db.query(Job).filter(Job.triage_status == "complete").all()

# For each job, find which target title it most likely matches
# by checking word overlap between job title and target titles
def best_matching_target(job_title, target_titles):
    job_title_lower = job_title.lower()
    job_words = set(job_title_lower.split())

    best_match = None
    best_score = 0

    for target in target_titles:
        target_lower = target.lower()
        target_words = set(target_lower.split())
        overlap = len(job_words & target_words)
        if overlap > best_score:
            best_score = overlap
            best_match = target

    return best_match if best_score > 0 else "Unmatched"

stats = defaultdict(lambda: {"Apply": 0, "Consider": 0, "Skip": 0, "Total": 0})

for job in jobs:
    verdict = (job.triage_result or {}).get("verdict", "Unknown")
    target = best_matching_target(job.title, target_titles)
    stats[target][verdict] += 1
    stats[target]["Total"] += 1

# Sort by total jobs descending
sorted_stats = sorted(stats.items(), key=lambda x: x[1]["Total"], reverse=True)

print(f"{'Target Title':<45} {'Total':>6} {'Apply':>6} {'Consider':>9} {'Skip':>6} {'Apply%':>7}")
print("-" * 85)

for target, counts in sorted_stats:
    total = counts["Total"]
    apply_count = counts["Apply"]
    consider_count = counts["Consider"]
    skip_count = counts["Skip"]
    apply_pct = (apply_count / total * 100) if total > 0 else 0
    print(f"{target[:44]:<45} {total:>6} {apply_count:>6} {consider_count:>9} {skip_count:>6} {apply_pct:>6.1f}%")

print()
print("Target titles in profile with ZERO jobs found:")
matched_targets = set(stats.keys())
for title in target_titles:
    if title not in matched_targets:
        print(f"  - {title}")

db.close()