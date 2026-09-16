import requests
import hashlib
import time
from datetime import datetime
from loguru import logger
from app.config import RAPIDAPI_KEY
from app.core.models import Job
from app.core.db import SessionLocal

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

def generate_external_id(title: str, company: str, location: str) -> str:
    title = (title or "").lower().strip()
    company = (company or "").lower().strip()
    location = (location or "").lower().strip()
    raw = f"{title}{company}{location}"
    return hashlib.md5(raw.encode()).hexdigest()

def clean_description(raw: str) -> str:
    if not raw:
        return ""
    import re
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_jobs(query: str, location: str = "United States", num_pages: int = 1) -> list:
    all_jobs = []
    for page in range(1, num_pages + 1):
        params = {
            "query": query,
            "location": location,
            "page": str(page),
            "num_pages": "1",
            "date_posted": "week"
        }
        try:
            response = requests.get(JSEARCH_URL, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            jobs = data.get("data", [])
            all_jobs.extend(jobs)
            logger.info(f"Fetched {len(jobs)} jobs for query: {query} page {page}")
        except Exception as e:
            logger.error(f"Error fetching jobs for query '{query}': {e}")
    return all_jobs

def save_jobs(raw_jobs: list) -> dict:
    db = SessionLocal()
    new_count = 0
    duplicate_count = 0
    seen_in_batch = set()

    try:
        for raw in raw_jobs:
            title = raw.get("job_title") or ""
            company = raw.get("employer_name") or ""
            location = raw.get("job_city") or raw.get("job_country") or ""
            external_id = generate_external_id(title, company, location)

            if external_id in seen_in_batch:
                duplicate_count += 1
                continue
            seen_in_batch.add(external_id)

            exists = db.query(Job).filter(Job.external_id == external_id).first()
            if exists:
                duplicate_count += 1
                continue

            description_raw = raw.get("job_description", "")
            description_cleaned = clean_description(description_raw)

            remote_type = "remote"
            if raw.get("job_is_remote"):
                remote_type = "remote"
            elif raw.get("job_city"):
                remote_type = "onsite"

            job = Job(
                external_id=external_id,
                title=title,
                company=company,
                location=location,
                remote_type=remote_type,
                posted_date=raw.get("job_posted_at_datetime_utc", ""),
                source="jsearch",
                url=raw.get("job_apply_link", "") or raw.get("job_google_link", ""),
                description_raw=description_raw,
                description_cleaned=description_cleaned,
                salary_min=raw.get("job_min_salary"),
                salary_max=raw.get("job_max_salary"),
                quality_flags=[],
                triage_status="pending"
            )
            db.add(job)
            new_count += 1

        db.commit()
        logger.info(f"Saved {new_count} new jobs. {duplicate_count} duplicates skipped.")
        return {"new": new_count, "duplicates": duplicate_count}

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving jobs: {e}")
        return {"new": 0, "duplicates": 0, "error": str(e)}
    finally:
        db.close()

def run_collection(target_titles: list, location: str = "United States") -> dict:
    total_new = 0
    total_duplicates = 0

    for i, title in enumerate(target_titles):
        raw_jobs = fetch_jobs(query=title, location=location)
        result = save_jobs(raw_jobs)
        total_new += result.get("new", 0)
        total_duplicates += result.get("duplicates", 0)
        if i < len(target_titles) - 1:
            time.sleep(2)

    return {"total_new": total_new, "total_duplicates": total_duplicates}