from typing import Iterable, List
import discord


def shorten(s: str, n: int = 260) -> str:
    s = (s or "").replace("\n", " ")
    return (s[: n - 1] + "…") if len(s) > n else s


def activity_texts(acts: Iterable[discord.Activity]) -> List[str]:
    texts: List[str] = []
    for a in acts or []:
        if isinstance(a, discord.CustomActivity):
            if getattr(a, "state", None):
                texts.append(str(a.state))
        elif getattr(a, "name", None):
            texts.append(str(a.name))
    return texts


def contains_any(haystack: str, needles: Iterable[str]) -> bool:
    s = (haystack or "").lower()
    return any(k in s for k in needles)

