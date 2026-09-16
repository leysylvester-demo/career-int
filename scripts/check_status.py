import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal
from app.core.models import Job

db = SessionLocal()
print("Pending:", db.query(Job).filter(Job.triage_status == "pending").count())
print("Complete:", db.query(Job).filter(Job.triage_status == "complete").count())
print("Failed:", db.query(Job).filter(Job.triage_status == "failed").count())
db.close()