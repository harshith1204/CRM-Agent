from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import pandas as pd
from fastapi import HTTPException
from pydantic import ValidationError

from .models import (
    Plan,
    MongoReadSpec,
    DataframeOpSpec,
    PlotSpec,
    ExcelSpec,
    MetabaseQuerySpec,
    MetabaseEmbedSpec,
    CreateTaskSpec,
    CreateNoteSpec,
    LogCallSpec,
    CreateActivitySpec,
    UpdateLeadSpec,
    ReportSpec,
    ToggleVehicleTypeSpec,
    VehicleTripFilterRequestSpec,
    TrackingLogRequestSpec,
    VehicleCancelTripSpec,
    AllocateStudentsToVehicleSpec,
    ChangeVehicleRouteStatusSpec,
    AllocateStaffToVehicleSpec,
)
from .tools import run_mongo, dataframe_ops, make_plot, export_excel, metabase_query_df, metabase_embed_url
from .storage import save_artifact
from .swagger_client import swagger


def _require_swagger():
    if swagger is None:
        raise HTTPException(status_code=503, detail="Swagger client not configured. Set SWAGGER_BASE_URL and SWAGGER_SPEC_URL.")


def create_task(spec: CreateTaskSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/tasks", method="post", body=spec.model_dump())


def create_note(spec: CreateNoteSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/notes", method="post", body=spec.model_dump())


def log_call(spec: LogCallSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/call-logs", method="post", body=spec.model_dump())


def create_activity(spec: CreateActivitySpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/activity", method="post", body=spec.model_dump())


def update_lead(spec: UpdateLeadSpec) -> Dict[str, Any]:
    _require_swagger()
    path = f"/leads/{spec.lead_id}"
    body = spec.fields
    return swagger.call(path=path, method="patch", body=body)


# Transport endpoints
def toggle_vehicle_type(spec: ToggleVehicleTypeSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-type-toggle", method="put", query={"id": spec.id, "isActive": spec.is_active})


def get_staff_transport_trips_paginated(spec: VehicleTripFilterRequestSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-tracking/trips/paged", method="put", body=spec.body)


def add_vehicle_tracking_log(spec: TrackingLogRequestSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-tracking/log", method="put", body=spec.body)


def vehicle_canceled(spec: VehicleCancelTripSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-tracking/cancel-trip", method="put", query={"tripId": spec.trip_id})


def allocate_students_to_vehicle(spec: AllocateStudentsToVehicleSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-route/students/allocate", method="put", body=spec.body)


def change_vehicle_route_status(spec: ChangeVehicleRouteStatusSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-route/status", method="put", query={"id": spec.id, "status": spec.status})


def allocate_staff_to_vehicle(spec: AllocateStaffToVehicleSpec) -> Dict[str, Any]:
    _require_swagger()
    return swagger.call(path="/vehicle-route/staff/allocate", method="put", body=spec.body)


def execute_plan(session_id: str, user_id: str, plan: Plan) -> Dict[str, Any]:
    audit: List[Dict[str, Any]] = []
    df_cache: Optional[pd.DataFrame] = None
    response: Dict[str, Any] = {"artifacts": {}, "preview_rows": [], "embed_urls": []}

    for tc in plan.tool_calls:
        audit.append({"at": datetime.now(timezone.utc).isoformat(), "tool": tc.tool, "args": tc.args})
        try:
            if tc.tool == "mongo.read":
                spec = MongoReadSpec(**tc.args)
                df_cache = run_mongo(user_id, spec)
                response["preview_rows"] = df_cache.head(10).to_dict(orient="records") if df_cache is not None else []
            elif tc.tool == "df.op":
                spec = DataframeOpSpec(**tc.args)
                df_cache = dataframe_ops(df_cache, spec)
                response["preview_rows"] = df_cache.head(10).to_dict(orient="records") if df_cache is not None else []
            elif tc.tool == "plot":
                spec = PlotSpec(**tc.args)
                png = make_plot(df_cache, spec)
                art_id = save_artifact(png, mime="image/png", filename="chart.png")
                response["artifacts"]["plot_png"] = {"artifact_id": art_id, "download_url": f"/artifacts/{art_id}"}
            elif tc.tool == "excel":
                spec = ExcelSpec(**tc.args)
                xlsx = export_excel(df_cache or pd.DataFrame(), spec)
                art_id = save_artifact(
                    xlsx,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename="report.xlsx",
                )
                response["artifacts"]["excel"] = {"artifact_id": art_id, "download_url": f"/artifacts/{art_id}"}
            elif tc.tool == "metabase.query":
                spec = MetabaseQuerySpec(**tc.args)
                df_cache = metabase_query_df(spec)
                response["preview_rows"] = df_cache.head(10).to_dict(orient="records") if df_cache is not None else []
            elif tc.tool == "metabase.embed":
                spec = MetabaseEmbedSpec(**tc.args)
                url = metabase_embed_url(spec)
                response["embed_urls"].append(url)
            elif tc.tool == "crm.create_task":
                out = create_task(CreateTaskSpec(**tc.args))
                response.setdefault("writes", []).append({"create_task": out})
            elif tc.tool == "crm.create_note":
                out = create_note(CreateNoteSpec(**tc.args))
                response.setdefault("writes", []).append({"create_note": out})
            elif tc.tool == "crm.log_call":
                out = log_call(LogCallSpec(**tc.args))
                response.setdefault("writes", []).append({"log_call": out})
            elif tc.tool == "crm.create_activity":
                out = create_activity(CreateActivitySpec(**tc.args))
                response.setdefault("writes", []).append({"create_activity": out})
            elif tc.tool == "crm.update_lead":
                out = update_lead(UpdateLeadSpec(**tc.args))
                response.setdefault("writes", []).append({"update_lead": out})
            elif tc.tool == "transport.toggle_vehicle_type":
                out = toggle_vehicle_type(ToggleVehicleTypeSpec(**tc.args))
                response.setdefault("writes", []).append({"toggle_vehicle_type": out})
            elif tc.tool == "transport.trips_paged":
                out = get_staff_transport_trips_paginated(VehicleTripFilterRequestSpec(**tc.args))
                response.setdefault("reads", []).append({"trips_paged": out})
            elif tc.tool == "transport.add_tracking_log":
                out = add_vehicle_tracking_log(TrackingLogRequestSpec(**tc.args))
                response.setdefault("writes", []).append({"add_tracking_log": out})
            elif tc.tool == "transport.cancel_trip":
                out = vehicle_canceled(VehicleCancelTripSpec(**tc.args))
                response.setdefault("writes", []).append({"cancel_trip": out})
            elif tc.tool == "transport.allocate_students":
                out = allocate_students_to_vehicle(AllocateStudentsToVehicleSpec(**tc.args))
                response.setdefault("writes", []).append({"allocate_students": out})
            elif tc.tool == "transport.change_route_status":
                out = change_vehicle_route_status(ChangeVehicleRouteStatusSpec(**tc.args))
                response.setdefault("writes", []).append({"change_route_status": out})
            elif tc.tool == "transport.allocate_staff":
                out = allocate_staff_to_vehicle(AllocateStaffToVehicleSpec(**tc.args))
                response.setdefault("writes", []).append({"allocate_staff": out})
            elif tc.tool == "report.build":
                from .reports import build_report

                spec = ReportSpec(**tc.args)
                xlsx = build_report(user_id, spec)
                art_id = save_artifact(
                    xlsx,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=f"{spec.title}.xlsx",
                )
                response["artifacts"]["report"] = {"artifact_id": art_id, "download_url": f"/artifacts/{art_id}"}
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool {tc.tool}")
        except ValidationError as ve:
            raise HTTPException(status_code=400, detail=f"Validation error for {tc.tool}: {ve}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tool execution error in {tc.tool}: {e}")

    response["message"] = plan.final_message or "Done."
    response["audit"] = audit
    return response


