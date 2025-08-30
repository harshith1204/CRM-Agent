from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import jwt
import pandas as pd
import requests
from fastapi import HTTPException

from .config import CFG, logger


class MetabaseClient:
    def __init__(self):
        self.site = (CFG.METABASE_SITE_URL or "").rstrip("/")
        self.session = requests.Session()
        self.session_token = CFG.METABASE_SESSION_TOKEN
        if not self.session_token and CFG.METABASE_USERNAME and CFG.METABASE_PASSWORD and self.site:
            try:
                self.login(CFG.METABASE_USERNAME, CFG.METABASE_PASSWORD)
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning(f"Metabase login failed: {e}")
        self.embed_secret = CFG.METABASE_EMBED_SECRET

    def login(self, username: str, password: str):
        url = f"{self.site}/api/session"
        resp = self.session.post(url, json={"username": username, "password": password}, timeout=20)
        resp.raise_for_status()
        self.session_token = resp.json().get("id")
        self.session.headers.update({"X-Metabase-Session": self.session_token})

    def query_card_json(self, card_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.site:
            raise HTTPException(status_code=503, detail="Metabase site not configured")
        if self.session_token:
            self.session.headers.update({"X-Metabase-Session": self.session_token})
        url = f"{self.site}/api/card/{card_id}/query"
        payload = {"parameters": params or {}}
        resp = self.session.post(url, json=payload, timeout=60)
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

    def query_card_dataframe(self, card_id: int, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        data = self.query_card_json(card_id, params)
        d = data.get("data") or data
        rows = d.get("rows", [])
        cols = [c.get("name") for c in d.get("cols", [])]
        if rows and cols:
            return pd.DataFrame(rows, columns=cols)
        if isinstance(d, dict) and "results" in d and isinstance(d["results"], list):
            return pd.DataFrame(d["results"])
        return pd.DataFrame(rows)

    def signed_embed_url(
        self,
        resource_type: str,
        resource_id: int,
        params: Optional[Dict[str, Any]] = None,
        theme: str = "light",
        expires_minutes: int = 60,
    ) -> str:
        if not self.embed_secret or not self.site:
            raise HTTPException(status_code=503, detail="Metabase embed secret or site URL not configured")
        assert resource_type in {"dashboard", "question"}
        payload = {
            "resource": {resource_type: resource_id},
            "params": params or {},
            "exp": int((datetime.utcnow() + timedelta(minutes=expires_minutes)).timestamp()),
        }
        token = jwt.encode(payload, self.embed_secret, algorithm="HS256")
        path = "/embed/dashboard/" if resource_type == "dashboard" else "/embed/question/"
        return f"{self.site}{path}{token}#theme={theme}&bordered=true&titled=true"


metabase = MetabaseClient()


