from datetime import date
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.jobs.expiry_checker import expire_schemes


def build_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.app_timezone))
    minute, hour, day, month, day_of_week = settings.expiry_check_cron.split()

    async def run_expiry_check() -> None:
        async with AsyncSessionLocal() as db:
            await expire_schemes(date.today(), db)

    scheduler.add_job(
        run_expiry_check,
        CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, timezone=ZoneInfo(settings.app_timezone)),
        id="expiry-check",
        replace_existing=True,
    )
    return scheduler

