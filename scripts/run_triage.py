import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from app.core.triage_engine import run_triage_batch
from app.core.job_filters import auto_skip_location_mismatches
from app.core.db import SessionLocal
from app.core.models import Profile

if __name__ == "__main__":
    db = SessionLocal()
    profile = db.query(Profile).first()
    location_prefs = profile.location_preferences if profile else []
    deal_breakers = profile.deal_breakers if profile else []
    db.close()

    logger.info("Running pre-triage location filter...")
    auto_skipped = auto_skip_location_mismatches(location_prefs, deal_breakers)
    logger.info(f"Auto-skipped {auto_skipped} jobs for location mismatch.")

    logger.info("Starting triage run...")
    result = run_triage_batch(batch_size=10)
    logger.info(f"Triage complete. Processed: {result['processed']}, Failed: {result['failed']}")