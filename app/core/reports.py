from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
import io
import pandas as pd

from .models import ReportSpec, ReportSheetSpec
from .tools import export_excel
from .db import MONGO_AVAILABLE, ctx, MOCK_DATA
from .models import MongoReadSpec
from .tools import run_mongo


def build_report(user_id: str, spec: ReportSpec) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        meta = pd.DataFrame([[spec.title, datetime.now(timezone.utc).isoformat()]], columns=["title", "generated_at"])
        meta.to_excel(writer, sheet_name="_meta", index=False)
        for sheet in spec.sheets:
            if sheet.source == "metabase_card" and sheet.metabase_card_id is not None:
                from .metabase_client import metabase

                df = metabase.query_card_dataframe(sheet.metabase_card_id, sheet.metabase_params)
            elif sheet.source == "mongo" and sheet.mongo_collection:
                df = run_mongo(user_id, MongoReadSpec(collection=sheet.mongo_collection, pipeline=sheet.mongo_pipeline, limit=20000))
            else:
                df = pd.DataFrame()
            df.to_excel(writer, sheet_name=sheet.name[:31] or "Sheet", index=False)
            ws = writer.sheets[sheet.name[:31] or "Sheet"]
            for i, col in enumerate(df.columns, start=1):
                width = 10
                if not df.empty:
                    width = max(10, min(60, int(df[col].astype(str).str.len().quantile(0.9)) + 3))
                ws.set_column(i, i, width)
    return buf.getvalue()

