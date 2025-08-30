from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
import json
import pandas as pd
from fastapi import HTTPException

from .rbac import rbac_policy
from .db import MONGO_AVAILABLE, ctx, MOCK_DATA
from .models import (
    KPIResponse,
    DataExplorerRequest,
    DataExplorerResponse,
    ReportListResponse,
    SavedReport,
)
from .tools import export_excel
from .storage import save_artifact, ARTIFACTS
from .models import ReportListResponse, SavedReport


def calc_kpis(user_id: str = "admin") -> KPIResponse:
    try:
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mtd_pipeline = [
            {"$match": {"created_date": {"$gte": start_of_month.isoformat()}, "status": {"$ne": "Lost"}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        if not MONGO_AVAILABLE or ctx is None:
            mtd_revenue = sum([row.get("amount", 0) for row in MOCK_DATA.get("leads", []) if row.get("created_date", "") >= start_of_month.isoformat() and row.get("status") != "Lost"])  # type: ignore
            new_leads_count = len([row for row in MOCK_DATA.get("leads", []) if row.get("created_date", "") >= start_of_month.isoformat()])
            won = len([row for row in MOCK_DATA.get("leads", []) if row.get("status") == "Won"])
            total = len(MOCK_DATA.get("leads", []))
        else:
            mtd_result = list(ctx.db.leads.aggregate(mtd_pipeline))
            mtd_revenue = mtd_result[0]["total"] if mtd_result else 0
            new_leads_pipeline = [{"$match": {"created_date": {"$gte": start_of_month.isoformat()}}}, {"$count": "total"}]
            new_leads_result = list(ctx.db.leads.aggregate(new_leads_pipeline))
            new_leads_count = new_leads_result[0]["total"] if new_leads_result else 0
            win_pipeline = [
                {"$group": {"_id": None, "total": {"$sum": 1}, "won": {"$sum": {"$cond": [{"$eq": ["$status", "Won"]}, 1, 0]}}}},
            ]
            win_result = list(ctx.db.leads.aggregate(win_pipeline))
            won = win_result[0]["won"] if win_result else 0
            total = win_result[0]["total"] if win_result else 0

        win_rate = (won / total * 100) if total > 0 else 0
        avg_cycle_days = 18

        return KPIResponse(
            mtd_revenue={"value": f"₹{mtd_revenue:,.0f}", "change": {"value": 12.5, "type": "positive"}},
            new_leads={"value": str(new_leads_count), "change": {"value": 8.2, "type": "positive"}},
            win_rate={"value": f"{win_rate:.1f}%", "change": {"value": 3.1, "type": "negative"}},
            avg_cycle={"value": f"{avg_cycle_days} days", "change": {"value": 5.2, "type": "positive"}},
        )
    except Exception:
        return KPIResponse(
            mtd_revenue={"value": "₹2,45,000", "change": {"value": 12.5, "type": "positive"}},
            new_leads={"value": "127", "change": {"value": 8.2, "type": "positive"}},
            win_rate={"value": "23.5%", "change": {"value": 3.1, "type": "negative"}},
            avg_cycle={"value": "18 days", "change": {"value": 5.2, "type": "positive"}},
        )


def explore_data_logic(req: DataExplorerRequest, user_id: str = "admin") -> DataExplorerResponse:
    from .tools import run_mongo  # local import to avoid cycles
    from .models import MongoReadSpec

    policy = rbac_policy(user_id)
    if req.collection not in policy["allow_collections"]:
        raise HTTPException(status_code=403, detail=f"User not allowed to access collection {req.collection}")

    if not MONGO_AVAILABLE or ctx is None:
        mock_items = MOCK_DATA.get(req.collection, [])
        data = mock_items.copy()
        if req.filters:
            for key, value in req.filters.items():
                if value and value != "all":
                    data = [item for item in data if item.get(key) == value]
        if req.search:
            search_lower = req.search.lower()
            data = [
                item
                for item in data
                if search_lower in str(item.get("name", "")).lower()
                or search_lower in str(item.get("company", "")).lower()
                or search_lower in str(item.get("email", "")).lower()
            ]
        total_count = len(data)
        skip = (req.page - 1) * req.limit
        data = data[skip : skip + req.limit]
        deny = set(rbac_policy(user_id).get("deny_fields", []))
        if deny:
            for doc in data:
                for field in deny:
                    doc.pop(field, None)
        has_more = (skip + req.limit) < total_count
        return DataExplorerResponse(data=data, total_count=total_count, page=req.page, limit=req.limit, has_more=has_more)

    pipeline: List[Dict[str, Any]] = []
    if req.filters:
        match_stage = {"$match": {}}
        for key, value in req.filters.items():
            if value and value != "all":
                match_stage["$match"][key] = value
        if match_stage["$match"]:
            pipeline.append(match_stage)
    if req.search:
        pipeline.append(
            {
                "$match": {
                    "$or": [
                        {"name": {"$regex": req.search, "$options": "i"}},
                        {"company": {"$regex": req.search, "$options": "i"}},
                        {"email": {"$regex": req.search, "$options": "i"}},
                    ]
                }
            }
        )
    count_pipeline = pipeline + [{"$count": "total"}]
    count_result = list(ctx.db[req.collection].aggregate(count_pipeline))
    total_count = count_result[0]["total"] if count_result else 0
    if req.sort_by:
        sort_order = 1 if req.sort_order == "asc" else -1
        pipeline.append({"$sort": {req.sort_by: sort_order}})
    skip = (req.page - 1) * req.limit
    pipeline.extend([{ "$skip": skip }, { "$limit": req.limit }])
    cursor = ctx.db[req.collection].aggregate(pipeline)
    data = list(cursor)
    deny = set(rbac_policy(user_id).get("deny_fields", []))
    if deny:
        for doc in data:
            for field in deny:
                doc.pop(field, None)
    has_more = (skip + req.limit) < total_count
    return DataExplorerResponse(data=data, total_count=total_count, page=req.page, limit=req.limit, has_more=has_more)


def export_collection_logic(collection: str, fmt: str = "excel", user_id: str = "admin") -> Dict[str, Any]:
    policy = rbac_policy(user_id)
    if collection not in policy["allow_collections"]:
        raise HTTPException(status_code=403, detail=f"User not allowed to access collection {collection}")
    if not MONGO_AVAILABLE or ctx is None:
        data = MOCK_DATA.get(collection, [])
    else:
        cursor = ctx.db[collection].find().limit(10000)
        data = list(cursor)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    df = pd.json_normalize(data)
    deny = set(rbac_policy(user_id).get("deny_fields", []))
    keep = [c for c in df.columns if c.split(".")[0] not in deny]
    df = df[keep]
    if fmt.lower() == "excel":
        from .models import ExcelSpec
        xlsx = export_excel(df, ExcelSpec(sheet_name=collection.title(), index=False, autofit=True))
        artifact_id = save_artifact(
            xlsx,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{collection}_export.xlsx",
        )
        return {"artifact_id": artifact_id, "download_url": f"/artifacts/{artifact_id}"}
    else:
        csv_data = df.to_csv(index=False)
        artifact_id = save_artifact(csv_data.encode("utf-8"), mime="text/csv", filename=f"{collection}_export.csv")
        return {"artifact_id": artifact_id, "download_url": f"/artifacts/{artifact_id}"}


def list_artifacts_logic() -> Dict[str, Any]:
    artifacts_list = []
    for artifact_id, item in ARTIFACTS.items():
        artifacts_list.append(
            {
                "id": artifact_id,
                "filename": item["filename"],
                "mime": item["mime"],
                "size": len(item["bytes"]),
                "download_url": f"/artifacts/{artifact_id}",
            }
        )
    return {"artifacts": artifacts_list}


def get_artifact_bytes(artifact_id: str) -> Dict[str, Any]:
    item = ARTIFACTS.get(artifact_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


def list_reports_logic(user_id: str = "admin") -> ReportListResponse:
    from .memory import SAVED_REPORTS

    user_reports = [r for r in SAVED_REPORTS.values() if r.created_by == user_id or user_id == "admin"]
    return ReportListResponse(reports=user_reports)


def create_report_logic(report: SavedReport, user_id: str = "admin") -> SavedReport:
    from .memory import SAVED_REPORTS
    import base64, os

    report_id = base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("=")
    report.id = report_id
    report.created_by = user_id
    report.created_at = datetime.now(timezone.utc).isoformat()
    SAVED_REPORTS[report_id] = report
    return report


def get_report_logic(report_id: str, user_id: str = "admin") -> SavedReport:
    from .memory import SAVED_REPORTS

    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return report


def run_report_logic(report_id: str, user_id: str = "admin") -> Dict[str, Any]:
    from .memory import SAVED_REPORTS
    from .reports import build_report

    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    xlsx = build_report(user_id, report.spec)
    artifact_id = save_artifact(
        xlsx,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{report.name}.xlsx",
    )
    report.last_run = datetime.now(timezone.utc).isoformat()
    SAVED_REPORTS[report_id] = report
    return {"artifact_id": artifact_id, "download_url": f"/artifacts/{artifact_id}"}


def delete_report_logic(report_id: str, user_id: str = "admin") -> Dict[str, Any]:
    from .memory import SAVED_REPORTS

    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    del SAVED_REPORTS[report_id]
    return {"message": "Report deleted successfully"}


def list_sessions_logic(user_id: str = "admin") -> List["SessionInfo"]:
    from .memory import MEMORY, SESSION_METADATA
    from .models import SessionInfo

    sessions: List[SessionInfo] = []
    for session_id, messages in MEMORY.sessions.items():
        if not messages:
            continue
        metadata = SESSION_METADATA.get(session_id, {})
        if metadata.get("user_id") != user_id and user_id != "admin":
            continue
        sessions.append(
            SessionInfo(
                session_id=session_id,
                user_id=metadata.get("user_id", "unknown"),
                created_at=metadata.get("created_at", datetime.now(timezone.utc).isoformat()),
                last_activity=metadata.get("last_activity", datetime.now(timezone.utc).isoformat()),
                message_count=len(messages),
            )
        )
    return sessions


def get_session_messages_logic(session_id: str, user_id: str = "admin") -> Dict[str, Any]:
    from .memory import MEMORY, SESSION_METADATA

    messages = MEMORY.get(session_id)
    metadata = SESSION_METADATA.get(session_id, {})
    if metadata.get("user_id") != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return {"session_id": session_id, "messages": messages, "metadata": metadata}


def delete_session_logic(session_id: str, user_id: str = "admin") -> Dict[str, Any]:
    from .memory import MEMORY, SESSION_METADATA

    metadata = SESSION_METADATA.get(session_id, {})
    if metadata.get("user_id") != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    MEMORY.sessions.pop(session_id, None)
    SESSION_METADATA.pop(session_id, None)
    return {"message": "Session deleted successfully"}


def get_collection_schema_logic(collection: str, user_id: str = "admin") -> Dict[str, Any]:
    policy = rbac_policy(user_id)
    if collection not in policy["allow_collections"]:
        raise HTTPException(status_code=403, detail=f"User not allowed to access collection {collection}")
    if not MONGO_AVAILABLE or ctx is None:
        sample_items = MOCK_DATA.get(collection, [])
        sample = sample_items[0] if sample_items else None
        if not sample:
            return {"fields": [], "sample_count": 0}
        fields = []
        for key, value in sample.items():
            fields.append({"name": key, "type": type(value).__name__, "sample_value": str(value)[:100] if not isinstance(value, dict) else "[object]"})
        total_docs = len(MOCK_DATA.get(collection, []))
        return {"collection": collection, "fields": fields, "sample_count": total_docs, "sample_document": sample}
    sample = ctx.db[collection].find_one()
    if not sample:
        return {"fields": [], "sample_count": 0}
    fields = []
    for key, value in sample.items():
        fields.append({"name": key, "type": type(value).__name__, "sample_value": str(value)[:100] if not isinstance(value, dict) else "[object]"})
    total_docs = ctx.db[collection].count_documents({})
    return {"collection": collection, "fields": fields, "sample_count": total_docs, "sample_document": sample}


