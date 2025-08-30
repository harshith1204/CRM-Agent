from __future__ import annotations

from typing import Any, Dict
import json

from .config import CFG
from .db import MONGO_AVAILABLE, ctx, MOCK_DATA


def build_schema_catalog() -> Dict[str, Any]:
    catalog = {}
    for name in CFG.ALLOWED_COLLECTIONS:
        try:
            if MONGO_AVAILABLE and ctx:
                sample = ctx.db[name].find_one()
                if not sample:
                    fields = []
                else:
                    fields = sorted(sample.keys())
            else:
                mock_items = MOCK_DATA.get(name, [])
                if mock_items:
                    fields = sorted(mock_items[0].keys())
                else:
                    fields = []
            catalog[name] = {"sample_fields": fields}
        except Exception:
            catalog[name] = {"sample_fields": []}
    return catalog


