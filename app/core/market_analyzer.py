from collections import Counter
from app.core.models import Job, Profile
from app.core.db import SessionLocal

def run_market_analysis() -> dict:
    db = SessionLocal()
    try:
        profile = db.query(Profile).first()
        jobs = db.query(Job).filter(Job.triage_status == "complete").all()

        if not jobs:
            return {"error": "No triaged jobs found"}

        # Verdict breakdown
        verdict_counts = Counter()
        for job in jobs:
            verdict = (job.triage_result or {}).get("verdict", "Unknown")
            verdict_counts[verdict] += 1

        # Company posting frequency (signals active hiring)
        company_counts = Counter()
        for job in jobs:
            if job.company:
                company_counts[job.company] += 1

        repeat_companies = [
            {"company": company, "postings": count}
            for company, count in company_counts.most_common(10)
            if count >= 2
        ]

        # Salary data from postings that include it
        salaries = []
        for job in jobs:
            if job.salary_min and job.salary_max:
                salaries.append((job.salary_min, job.salary_max))

        salary_stats = None
        if salaries:
            mins = [s[0] for s in salaries]
            maxs = [s[1] for s in salaries]
            salary_stats = {
                "jobs_with_salary_data": len(salaries),
                "total_jobs": len(jobs),
                "avg_min": sum(mins) // len(mins),
                "avg_max": sum(maxs) // len(maxs),
                "overall_min": min(mins),
                "overall_max": max(maxs)
            }

            if profile and profile.compensation_floor:
                below_floor = sum(1 for mx in maxs if mx < profile.compensation_floor)
                salary_stats["postings_below_floor"] = below_floor
                salary_stats["compensation_floor"] = profile.compensation_floor

        # Remote vs onsite breakdown
        remote_counts = Counter()
        for job in jobs:
            remote_counts[job.remote_type or "unknown"] += 1

        # Apply-tier jobs by title pattern (rough grouping)
        apply_jobs = [j for j in jobs if (j.triage_result or {}).get("verdict") == "Apply"]
        apply_titles = Counter()
        for job in apply_jobs:
            words = job.title.split()[:3]
            apply_titles[" ".join(words)] += 1

        return {
            "total_jobs": len(jobs),
            "verdict_breakdown": dict(verdict_counts),
            "repeat_companies": repeat_companies,
            "salary_stats": salary_stats,
            "remote_breakdown": dict(remote_counts),
            "top_apply_title_patterns": apply_titles.most_common(10)
        }

    finally:
        db.close()