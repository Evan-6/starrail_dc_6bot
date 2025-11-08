import os
from typing import List, Optional


def _get_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y"}


# Core bot settings
COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# Channels / Guild
CHANNEL_ID: Optional[int] = None
try:
    _cid = os.getenv("CHANNEL_ID")
    CHANNEL_ID = int(_cid) if _cid else None
except Exception:
    CHANNEL_ID = None

GUILD_ID: Optional[int] = None
try:
    _gid = os.getenv("GUILD_ID")
    GUILD_ID = int(_gid) if _gid else None
except Exception:
    GUILD_ID = None


# Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


# Presence monitor
PRESENCE_ENABLED: bool = _get_bool("PRESENCE_ENABLED", "false")
PRESENCE_COOLDOWN_MIN: int = int(os.getenv("PRESENCE_COOLDOWN_MIN", "120"))

PRESENCE_KEYWORDS: List[str] = [
    k.strip().lower()
    for k in os.getenv(
        "PRESENCE_KEYWORDS",
        "honkai;star rail;崩壞;崩坏;崩壊;星穹;星鐵;星铁",
    ).split(";")
    if k.strip()
]


# Scheduler / time
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Taipei")

