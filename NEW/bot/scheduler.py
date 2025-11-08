import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from NEW import config


scheduler = BackgroundScheduler()
_started = False
_bot_loop = None  # type: Optional[asyncio.AbstractEventLoop]


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _bot_loop
    _bot_loop = loop


async def _send_weekly_message(bot) -> None:
    if not config.CHANNEL_ID:
        return
    channel = bot.get_channel(int(config.CHANNEL_ID))
    if channel:
        await channel.send("@here 記得打模擬宇宙ʕ•̫͡•ʔ•̫͡•ʔ•̫͡•ʕ•̫͡•ʔ•̫͡•ʔ")


def _weekly_job(bot):
    if _bot_loop is None:
        return
    fut = asyncio.run_coroutine_threadsafe(_send_weekly_message(bot), _bot_loop)
    try:
        fut.result(timeout=30)
    except Exception:
        pass


def init_jobs(bot) -> None:
    # Clear existing then add cron job
    for job in list(scheduler.get_jobs()):
        try:
            scheduler.remove_job(job.id)
        except Exception:
            pass

    scheduler.add_job(
        _weekly_job,
        id="weekly_reminder",
        trigger="cron",
        day_of_week="sun",
        hour=9,
        minute=0,
        timezone=config.TIMEZONE,
        args=[bot],
        replace_existing=True,
    )


def ensure_started() -> None:
    global _started
    if not _started:
        scheduler.start()
        _started = True


def status_text() -> str:
    # Minimal status reporter for commands
    from apscheduler.schedulers.base import (
        STATE_RUNNING,
        STATE_PAUSED,
        STATE_STOPPED,
    )

    state = scheduler.state
    if state == STATE_RUNNING:
        state_text = "Running"
    elif state == STATE_PAUSED:
        state_text = "Paused"
    elif state == STATE_STOPPED:
        state_text = "Stopped"
    else:
        state_text = str(state)

    job = scheduler.get_job("weekly_reminder")
    next_run = (
        "無"
        if not job or not job.next_run_time
        else job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    )
    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"📊 狀態\n- Scheduler：{state_text}\n- 下一次排程：{next_run}\n- 現在時間：{now_text}"

