import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED

from NEW import config
from NEW.utils import schedule_store


scheduler = BackgroundScheduler()
_started = False
_bot_loop: Optional[asyncio.AbstractEventLoop] = None
_bot_instance: Optional[Any] = None


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _bot_loop
    _bot_loop = loop


async def _send_message(job_conf: Dict[str, Any]) -> None:
    if _bot_instance is None:
        return
    channel_id = job_conf.get("channel_id")
    if not channel_id:
        return
    channel = _bot_instance.get_channel(int(channel_id))
    if channel is None:
        return
    message = job_conf.get("message") or schedule_store.DEFAULT_MESSAGE
    await channel.send(message)


def _job_runner(job_conf: Dict[str, Any]) -> None:
    if _bot_loop is None:
        return
    fut = asyncio.run_coroutine_threadsafe(_send_message(job_conf), _bot_loop)
    try:
        fut.result(timeout=30)
    except Exception:
        pass


def _clear_jobs() -> None:
    for job in list(scheduler.get_jobs()):
        try:
            scheduler.remove_job(job.id)
        except Exception:
            pass


def _schedule_jobs() -> None:
    cfg = schedule_store.load_config()
    default_tz = cfg.get("timezone") or config.TIMEZONE
    _clear_jobs()

    for job_conf in cfg.get("jobs", []):
        if not job_conf.get("enabled", True):
            continue
        if not job_conf.get("channel_id"):
            continue
        tz_name = job_conf.get("timezone") or default_tz
        job_id = f"schedule::{job_conf.get('id')}"

        try:
            scheduler.add_job(
                _job_runner,
                id=job_id,
                trigger="cron",
                day_of_week=job_conf.get("day_of_week", "sun"),
                hour=int(job_conf.get("hour", 9)),
                minute=int(job_conf.get("minute", 0)),
                timezone=tz_name,
                args=[job_conf],
                replace_existing=True,
            )
        except Exception:
            continue


def init_jobs(bot) -> None:
    global _bot_instance
    _bot_instance = bot
    _schedule_jobs()


def refresh_jobs() -> None:
    if _bot_instance is None:
        return
    _schedule_jobs()


def run_job_now(job_id: str) -> bool:
    job_conf = schedule_store.get_job(job_id)
    if not job_conf or not job_conf.get("channel_id"):
        return False
    if _bot_loop is None:
        return False
    fut = asyncio.run_coroutine_threadsafe(_send_message(job_conf), _bot_loop)
    try:
        fut.result(timeout=30)
        return True
    except Exception:
        return False


def ensure_started() -> None:
    global _started
    if not _started:
        scheduler.start()
        _started = True


def status_text() -> str:
    if scheduler.state == STATE_RUNNING:
        state_text = "Running"
    elif scheduler.state == STATE_PAUSED:
        state_text = "Paused"
    elif scheduler.state == STATE_STOPPED:
        state_text = "Stopped"
    else:
        state_text = str(scheduler.state)

    jobs = scheduler.get_jobs()
    if not jobs:
        jobs_lines = "- （尚未建立排程或皆已停用）"
    else:
        parts = []
        for job in jobs:
            next_run = "暫無"
            if job.next_run_time:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            parts.append(f"- {job.id.replace('schedule::', '')}：{next_run}")
        jobs_lines = "\n".join(parts)

    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    cfg_path = schedule_store.config_path()
    return (
        "排程狀態\n"
        f"- Scheduler：{state_text}\n"
        f"{jobs_lines}\n"
        f"- 目前時間：{now_text}\n"
        f"- 設定檔：{cfg_path}"
    )
