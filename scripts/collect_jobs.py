import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.core.job_collector import run_collection
from app.core.job_filters import flag_low_quality_jobs
from app.core.db import SessionLocal
from app.core.models import Profile

def get_target_titles() -> list:
    db = SessionLocal()
    try:
        profile = db.query(Profile).first()
        if profile and profile.target_titles:
            return profile.target_titles
        return [
            "Director of Enablement",
            "Principal Enablement",
            "Head of AI Architect",
            "Technical Program Manager",
            "Director of Learning and Development"
        ]
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting job collection...")
    titles = get_target_titles()
    logger.info(f"Collecting jobs for {len(titles)} target titles: {titles}")
    result = run_collection(target_titles=titles)
    logger.info(f"Collection complete: {result['total_new']} new jobs, {result['total_duplicates']} duplicates")
    logger.info("Running quality filter...")
    flagged = flag_low_quality_jobs()
    logger.info(f"Quality filter complete. {flagged} jobs flagged.")
