"""
Run aging job directly — use this as a cPanel cron job instead of
relying on the Passenger lifespan scheduler.

Set up in cPanel Cron Jobs:
  Command: /home/wykqfeio/virtualenv/jiinueloan/3.11/bin/python /home/wykqfeio/jiinueloan/run_aging.py
  Schedule: Once daily at midnight (0 0 * * *)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.database import SessionLocal
from app.services.aging import run_aging_job
from datetime import date

print(f"Running aging job for {date.today()}")
db = SessionLocal()
try:
    run_aging_job(db=db)
    print("Aging job completed successfully.")
except Exception as e:
    print(f"Aging job failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
