import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from NEW import config


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CONFIG_PATH = DATA_DIR / "schedules.json"
DEFAULT_MESSAGE = "@here 記得模一下宇宙ʕ·ᴥ·ʔ"

_DAY_ALIASES = {
    "mon": "mon",
    "monday": "mon",
    "週一": "mon",
    "星期一": "mon",
    "tue": "tue",
    "tuesday": "tue",
    "週二": "tue",
    "星期二": "tue",
    "wed": "wed",
    "wednesday": "wed",
    "週三": "wed",
    "星期三": "wed",
    "thu": "thu",
    "thursday": "thu",
    "週四": "thu",
    "星期四": "thu",
    "fri": "fri",
    "friday": "fri",
    "週五": "fri",
    "星期五": "fri",
    "sat": "sat",
    "saturday": "sat",
    "週六": "sat",
    "星期六": "sat",
    "sun": "sun",
    "sunday": "sun",
    "週日": "sun",
    "星期日": "sun",
}


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def _normalize_day(value: Optional[str]) -> str:
    if not value:
        return "sun"
    lowered = value.strip().lower()
    return _DAY_ALIASES.get(lowered, "sun")


def _safe_channel_id(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        cid = int(value)
    except (TypeError, ValueError):
        return None
    return cid if cid > 0 else None


def _normalize_job(index: int, job: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(job.get("id") or f"job_{index + 1}")
    channel_id = _safe_channel_id(job.get("channel_id"))
    hour = _clamp(int(job.get("hour", 9)), 0, 23)
    minute = _clamp(int(job.get("minute", 0)), 0, 59)
    description = str(job.get("description") or "").strip()
    timezone = str(job.get("timezone")).strip() if job.get("timezone") else None

    return {
        "id": job_id,
        "description": description,
        "channel_id": channel_id,
        "day_of_week": _normalize_day(job.get("day_of_week")),
        "hour": hour,
        "minute": minute,
        "message": str(job.get("message") or DEFAULT_MESSAGE),
        "enabled": bool(job.get("enabled", True)),
        "timezone": timezone,
    }


def _default_job() -> Dict[str, Any]:
    return {
        "id": "weekly_reminder",
        "description": "每週提醒：週日 09:00 模一下宇宙",
        "channel_id": config.CHANNEL_ID,
        "day_of_week": "sun",
        "hour": 9,
        "minute": 0,
        "message": DEFAULT_MESSAGE,
        "enabled": bool(config.CHANNEL_ID),
        "timezone": None,
    }


def _default_config() -> Dict[str, Any]:
    return {"timezone": config.TIMEZONE, "jobs": [_default_job()]}


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    timezone = str(data.get("timezone") or config.TIMEZONE)
    jobs = data.get("jobs") or []
    normalized_jobs = []
    seen_ids = set()
    for idx, raw in enumerate(jobs):
        if not isinstance(raw, dict):
            continue
        job = _normalize_job(idx, raw)
        base = job["id"]
        suffix = 2
        while job["id"] in seen_ids:
            job["id"] = f"{base}-{suffix}"
            suffix += 1
        seen_ids.add(job["id"])
        normalized_jobs.append(job)

    return {"timezone": timezone, "jobs": normalized_jobs}


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return save_config(_default_config())
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return save_config(_default_config())
    return _normalize(raw)


def save_config(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _normalize(data)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return normalized


def get_jobs() -> List[Dict[str, Any]]:
    return deepcopy(load_config().get("jobs", []))


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    target = str(job_id)
    for job in load_config().get("jobs", []):
        if job.get("id") == target:
            return deepcopy(job)
    return None


def config_path() -> Path:
    return CONFIG_PATH


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def generate_job_id(name: str, existing_ids: Optional[List[str]] = None) -> str:
    existing = {s for s in (existing_ids or []) if s}
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    if not slug:
        slug = "schedule"
    candidate = slug
    counter = 2
    while candidate in existing:
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


__all__ = [
    "CONFIG_PATH",
    "DEFAULT_MESSAGE",
    "config_path",
    "generate_job_id",
    "get_job",
    "get_jobs",
    "load_config",
    "save_config",
]
