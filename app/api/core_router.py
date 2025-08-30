from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from app.core import core


router = APIRouter(prefix="/core", tags=["core"])


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


@router.get("/kpis")
def get_kpis(user_id: str = "admin"):
    return core.calc_kpis(user_id)


class DataExplorerRequest(core.DataExplorerRequest):
    pass


@router.post("/data/explore")
def explore_data(req: DataExplorerRequest, user_id: str = "admin"):
    return core.explore_data_logic(req, user_id)


@router.get("/data/export/{collection}")
def export_collection_data(collection: str, format: str = "excel", user_id: str = "admin"):
    return core.export_collection_logic(collection, format, user_id)


@router.get("/reports")
def list_reports(user_id: str = "admin"):
    return core.list_reports_logic(user_id)


class SavedReport(core.SavedReport):
    pass


@router.post("/reports")
def create_report(report: SavedReport, user_id: str = "admin"):
    return core.create_report_logic(report, user_id)


@router.get("/reports/{report_id}")
def get_report(report_id: str, user_id: str = "admin"):
    return core.get_report_logic(report_id, user_id)


@router.post("/reports/{report_id}/run")
def run_report(report_id: str, user_id: str = "admin"):
    return core.run_report_logic(report_id, user_id)


@router.delete("/reports/{report_id}")
def delete_report(report_id: str, user_id: str = "admin"):
    return core.delete_report_logic(report_id, user_id)


@router.get("/sessions")
def list_sessions(user_id: str = "admin"):
    return core.list_sessions_logic(user_id)


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, user_id: str = "admin"):
    return core.get_session_messages_logic(session_id, user_id)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, user_id: str = "admin"):
    return core.delete_session_logic(session_id, user_id)


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str):
    item = core.get_artifact_bytes(artifact_id)
    return StreamingResponse(
        io.BytesIO(item["bytes"]),
        media_type=item["mime"],
        headers={"Content-Disposition": f"attachment; filename={item['filename']}"},
    )


@router.get("/artifacts")
def list_artifacts():
    return core.list_artifacts_logic()


@router.get("/collections/{collection}/schema")
def get_collection_schema(collection: str, user_id: str = "admin"):
    return core.get_collection_schema_logic(collection, user_id)


@router.post("/plan")
def plan_only(req: ChatRequest):
    return core.plan_only_logic(req.session_id, req.user_id, req.message)


@router.post("/chat")
def chat(req: ChatRequest):
    # LangGraph chat remains in /agent; this provides core-only flow mirroring legacy behavior
    schema_catalog = core.build_schema_catalog()
    history = core.MEMORY.get(req.session_id)
    history.append({"role": "user", "content": req.message})
    plan = core.client.plan(
        system=(core.SYSTEM_PROMPT + f"\nSchema catalog: {core.json.dumps(schema_catalog)[:2000]}"),
        messages=history,
        tools_schema=core.TOOLS_SCHEMA,
    )
    result = core.execute_plan(req.session_id, req.user_id, plan)
    current_time = core.datetime.now(core.timezone.utc).isoformat()
    core.MEMORY.append(req.session_id, "assistant", result.get("message", ""))
    return {
        "message": result.get("message", ""),
        "preview_rows": result.get("preview_rows", []),
        "artifacts": result.get("artifacts", {}),
        "embed_urls": result.get("embed_urls", []),
        "plan": plan.model_dump(),
        "schema_catalog": schema_catalog,
        "timestamp": current_time,
        "session_info": core.SESSION_METADATA.get(req.session_id, {}),
    }

