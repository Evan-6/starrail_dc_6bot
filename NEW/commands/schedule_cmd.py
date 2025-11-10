import discord
from discord import app_commands
from discord.ext import commands

from NEW.bot import scheduler as sched
from NEW.utils import schedule_store


DAY_CHOICES = [
    app_commands.Choice(name="週一 (Mon)", value="mon"),
    app_commands.Choice(name="週二 (Tue)", value="tue"),
    app_commands.Choice(name="週三 (Wed)", value="wed"),
    app_commands.Choice(name="週四 (Thu)", value="thu"),
    app_commands.Choice(name="週五 (Fri)", value="fri"),
    app_commands.Choice(name="週六 (Sat)", value="sat"),
    app_commands.Choice(name="週日 (Sun)", value="sun"),
]


def _format_job(job: dict, timezone: str) -> str:
    status = "✅" if job.get("enabled", True) else "⏸️"
    channel = (
        f"<#{int(job['channel_id'])}>"
        if job.get("channel_id")
        else "(未設定頻道)"
    )
    desc = job.get("description") or ""
    tz = job.get("timezone") or timezone or "UTC"
    day = job.get("day_of_week", "?")
    hour = int(job.get("hour", 0))
    minute = int(job.get("minute", 0))
    message = (job.get("message") or "").replace("\n", " ")
    if len(message) > 90:
        message = message[:87] + "..."
    return (
        f"{status} `{job.get('id')}` {day} "
        f"{hour:02d}:{minute:02d} {tz} → {channel}\n"
        f"內容：{message or '(未設定訊息)'}"
        + (f"\n備註：{desc}" if desc else "")
    )


def _trim_message(text: str) -> str:
    cleaned = text.strip()
    return cleaned[:1900]


class ScheduleCog(commands.Cog):
    group = app_commands.Group(name="schedule", description="管理排程提醒")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @group.command(name="list", description="查看目前排程設定")
    @app_commands.describe(private="是否僅自己可見")
    async def schedule_list(
        self, interaction: discord.Interaction, private: bool = True
    ):
        data = schedule_store.load_config()
        timezone = data.get("timezone") or "UTC"
        jobs = data.get("jobs", [])

        if not jobs:
            text = f"目前沒有排程。時區：{timezone}"
        else:
            parts = [f"時區：{timezone}", ""]
            for job in jobs:
                parts.append(_format_job(job, timezone))
                parts.append("")
            text = "\n".join(parts).strip()

        await interaction.response.send_message(text, ephemeral=private)

    @group.command(name="create", description="新增排程")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        name="排程識別名稱",
        channel="要送訊息的頻道",
        day="觸發星期",
        hour="觸發小時 (0-23)",
        minute="觸發分鐘 (0-59)",
        message="要送出的文字",
        enabled="是否啟用",
        timezone="覆寫單一排程時區 (可空白)",
        description="備註說明 (可空白)",
    )
    @app_commands.choices(day=DAY_CHOICES)
    async def schedule_create(
        self,
        interaction: discord.Interaction,
        name: str,
        channel: discord.TextChannel,
        day: app_commands.Choice[str],
        hour: app_commands.Range[int, 0, 23],
        minute: app_commands.Range[int, 0, 59],
        message: str,
        enabled: bool = True,
        timezone: str | None = None,
        description: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        cfg = schedule_store.load_config()
        job_ids = [job.get("id") for job in cfg.get("jobs", [])]
        job_id = schedule_store.generate_job_id(name, job_ids)
        new_job = {
            "id": job_id,
            "description": (description or "").strip(),
            "channel_id": channel.id,
            "day_of_week": day.value,
            "hour": int(hour),
            "minute": int(minute),
            "message": _trim_message(message),
            "enabled": bool(enabled),
            "timezone": (timezone or "").strip() or None,
        }
        cfg.setdefault("jobs", []).append(new_job)
        schedule_store.save_config(cfg)
        sched.refresh_jobs()
        tz = cfg.get("timezone") or "UTC"
        text = f"已新增排程 `{job_id}`\n" + _format_job(new_job, tz)
        await interaction.followup.send(text, ephemeral=True)

    @group.command(name="update", description="更新排程設定")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        job_id="要更新的排程 ID",
        channel="新的頻道 (空白則不變)",
        day="新的星期 (空白則不變)",
        hour="新的小時",
        minute="新的分鐘",
        message="新的訊息內容",
        enabled="啟用或停用",
        timezone="覆寫該排程時區",
        description="更新備註",
    )
    @app_commands.choices(day=DAY_CHOICES)
    async def schedule_update(
        self,
        interaction: discord.Interaction,
        job_id: str,
        channel: discord.TextChannel | None = None,
        day: app_commands.Choice[str] | None = None,
        hour: app_commands.Range[int, 0, 23] | None = None,
        minute: app_commands.Range[int, 0, 59] | None = None,
        message: str | None = None,
        enabled: bool | None = None,
        timezone: str | None = None,
        description: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        cfg = schedule_store.load_config()
        jobs = cfg.get("jobs", [])
        target = next((job for job in jobs if job.get("id") == job_id), None)
        if target is None:
            await interaction.followup.send("找不到此排程 ID。", ephemeral=True)
            return

        if channel is not None:
            target["channel_id"] = channel.id
        if day is not None:
            target["day_of_week"] = day.value
        if hour is not None:
            target["hour"] = int(hour)
        if minute is not None:
            target["minute"] = int(minute)
        if message is not None:
            target["message"] = _trim_message(message)
        if enabled is not None:
            target["enabled"] = bool(enabled)
        if timezone is not None:
            trimmed = timezone.strip()
            target["timezone"] = trimmed or None
        if description is not None:
            target["description"] = description.strip()

        schedule_store.save_config(cfg)
        sched.refresh_jobs()
        tz = cfg.get("timezone") or "UTC"
        text = f"已更新 `{job_id}`\n" + _format_job(target, tz)
        await interaction.followup.send(text, ephemeral=True)

    @group.command(name="delete", description="刪除排程")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(job_id="要刪除的排程 ID")
    async def schedule_delete(self, interaction: discord.Interaction, job_id: str):
        await interaction.response.defer(ephemeral=True)
        cfg = schedule_store.load_config()
        jobs = cfg.get("jobs", [])
        before = len(jobs)
        jobs = [job for job in jobs if job.get("id") != job_id]
        if len(jobs) == before:
            await interaction.followup.send("找不到此排程 ID。", ephemeral=True)
            return
        cfg["jobs"] = jobs
        schedule_store.save_config(cfg)
        sched.refresh_jobs()
        await interaction.followup.send(f"已刪除 `{job_id}`。", ephemeral=True)

    @group.command(name="run", description="立即執行指定排程")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(job_id="要立即執行的排程 ID")
    async def schedule_run(self, interaction: discord.Interaction, job_id: str):
        await interaction.response.defer(ephemeral=True)
        ok = sched.run_job_now(job_id)
        if ok:
            await interaction.followup.send(f"已觸發 `{job_id}`。", ephemeral=True)
        else:
            await interaction.followup.send(
                "觸發失敗，請確認排程是否存在且有設定頻道。", ephemeral=True
            )

    @schedule_update.autocomplete("job_id")
    @schedule_delete.autocomplete("job_id")
    @schedule_run.autocomplete("job_id")
    async def job_id_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        del interaction
        current_lower = current.lower()
        jobs = schedule_store.get_jobs()
        items = []
        for job in jobs:
            job_id = job.get("id", "")
            if current_lower not in job_id.lower():
                continue
            name = job_id
            if job.get("description"):
                name = f"{job_id} · {job['description']}"
            items.append(app_commands.Choice(name=name[:100], value=job_id))
            if len(items) == 25:
                break
        return items


async def setup(bot: commands.Bot):
    cog = ScheduleCog(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(ScheduleCog.group)
    except Exception:
        pass
