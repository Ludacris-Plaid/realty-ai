import asyncio
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apps.worker.src.db import get_or_create_bot_config
from packages.ai.briefing import generate_briefing
from apps.worker.src.notifications import create_notification_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check():
    logger.info("Worker health check performed.")

async def daily_briefing():
    try:
        briefing = generate_briefing("Athena")
        logger.info("Daily briefing generated:\n%s", briefing)
        
        # Send via notification manager (email if configured)
        nm = create_notification_manager()
        await nm.send_briefing(briefing)
    except Exception as e:
        logger.exception("Daily briefing failed: %s", e)

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(health_check, 'interval', minutes=10, replace_existing=True)
    scheduler.add_job(daily_briefing, CronTrigger(hour=6, minute=0), replace_existing=True)
    
    logger.info("Initializing worker config...")
    await get_or_create_bot_config("athena_worker_primary")
    
    scheduler.start()
    logger.info("Worker started. Daily briefing scheduled for 06:00 UTC.")
    
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Worker shut down.")

if __name__ == "__main__":
    asyncio.run(main())
