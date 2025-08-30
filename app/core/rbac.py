from __future__ import annotations

from typing import Any, Dict
from .config import CFG


def rbac_policy(user_id: str) -> Dict[str, Any]:
    return {
        "allow_collections": list(CFG.ALLOWED_COLLECTIONS),
        "deny_fields": ["ssn", "salary"],
        "role": "admin" if user_id in {"admin", "alice"} else "analyst",
    }

