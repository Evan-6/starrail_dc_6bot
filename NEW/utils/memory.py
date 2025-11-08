from typing import Deque, Dict, List, Tuple
from collections import deque


class ChannelMemory:
    def __init__(self, max_chars: int = 4000, max_turns: int = 8):
        self.max_chars = max_chars
        self.max_turns = max_turns
        self.turns: Deque[Tuple[str, str]] = deque()  # (role, text)

    def add(self, role: str, text: str) -> None:
        self.turns.append((role, text))
        while len(self.turns) > self.max_turns:
            self.turns.popleft()
        while self.total_chars() > self.max_chars and self.turns:
            self.turns.popleft()

    def total_chars(self) -> int:
        return sum(len(t) for _, t in self.turns)

    def as_lines(self) -> List[str]:
        return [f"{role.upper()}: {text}" for role, text in self.turns]


_MEMORIES: Dict[int, ChannelMemory] = {}


def get_memory(channel_id: int) -> ChannelMemory:
    if channel_id not in _MEMORIES:
        _MEMORIES[channel_id] = ChannelMemory()
    return _MEMORIES[channel_id]

def clear_memory(channel_id: int) -> None:
    _MEMORIES.pop(channel_id, None)

