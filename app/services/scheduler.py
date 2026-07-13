"""
Scheduler service — runs background jobs like aging.
Hooks into FastAPI lifecycle.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR

from app.services.aging import run_aging_job

logger = logging.getLogger(__name__)
_scheduler = None


def _on_job_error(event):
    logger.error(f"[Scheduler] Job {event.job_id} failed: {event.exception}")


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    # Run aging job every midnight
    _scheduler.add_job(
        run_aging_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="nightly_aging_job",
        name="Nightly Loan Aging and Penalties",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("✅ APScheduler started. Nightly aging job registered.")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        logger.info("🛑 APScheduler shut down.")
