from __future__ import annotations

from typing import Any, Dict
import base64


ARTIFACTS: Dict[str, Dict[str, Any]] = {}


def save_artifact(payload: bytes, *, mime: str, filename: str) -> str:
    artifact_id = base64.urlsafe_b64encode(__import__("os").urandom(12)).decode("utf-8").rstrip("=")
    ARTIFACTS[artifact_id] = {"bytes": payload, "mime": mime, "filename": filename}
    return artifact_id

