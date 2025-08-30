from __future__ import annotations

from typing import Any, Dict, List


class ChatMemory:
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

    def get(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions.setdefault(session_id, [])

    def append(self, session_id: str, role: str, content: str):
        self.sessions.setdefault(session_id, []).append({"role": role, "content": content})


MEMORY = ChatMemory()

# In-memory storage for reports and sessions
SAVED_REPORTS: Dict[str, Any] = {}
SESSION_METADATA: Dict[str, Any] = {}

