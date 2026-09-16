import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal
from app.core.models import Job

db = SessionLocal()
count = db.query(Job).filter(Job.triage_status == "failed").update({"triage_status": "pending"})
db.commit()
print(f"Reset {count} failed jobs to pending.")
db.close()