from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# Tool Schemas
class MongoReadSpec(BaseModel):
    collection: str
    pipeline: List[Dict[str, Any]] = Field(default_factory=list)
    limit: int = Field(default=1000, ge=1, le=20000)


class DataframeOpSpec(BaseModel):
    operation: str  # select|filter|sort|groupby|pivot
    params: Dict[str, Any] = Field(default_factory=dict)


class PlotSpec(BaseModel):
    kind: str  # bar|line|pie|scatter
    x: Optional[str] = None
    y: Optional[str] = None
    agg: Optional[str] = "sum"
    title: Optional[str] = None


class ExcelSpec(BaseModel):
    sheet_name: str = "Sheet1"
    index: bool = False
    autofit: bool = True


# Write tools (CRM actions)
class CreateTaskSpec(BaseModel):
    title: str
    due_date: Optional[str] = None
    lead_id: Optional[str] = None
    owner_id: Optional[str] = None
    priority: Optional[str] = None


class CreateNoteSpec(BaseModel):
    lead_id: str
    body: str


class LogCallSpec(BaseModel):
    lead_id: str
    direction: str  # outbound|inbound
    duration_seconds: Optional[int] = None
    summary: Optional[str] = None


class CreateActivitySpec(BaseModel):
    lead_id: str
    type: str  # email|meeting|demo|followup
    when: Optional[str] = None
    notes: Optional[str] = None


class UpdateLeadSpec(BaseModel):
    lead_id: str
    fields: Dict[str, Any]


# Transport tools
class ToggleVehicleTypeSpec(BaseModel):
    id: str
    is_active: bool


class VehicleTripFilterRequestSpec(BaseModel):
    body: Dict[str, Any] = Field(default_factory=dict)


class TrackingLogRequestSpec(BaseModel):
    body: Dict[str, Any] = Field(default_factory=dict)


class VehicleCancelTripSpec(BaseModel):
    trip_id: str


class AllocateStudentsToVehicleSpec(BaseModel):
    body: Dict[str, Any] = Field(default_factory=dict)


class ChangeVehicleRouteStatusSpec(BaseModel):
    id: str
    status: Literal["ACTIVE", "INACTIVE", "UNDER_MAINTENANCE"]


class AllocateStaffToVehicleSpec(BaseModel):
    body: Dict[str, Any] = Field(default_factory=dict)


# Metabase tools
class MetabaseQuerySpec(BaseModel):
    card_id: int
    params: Dict[str, Any] = Field(default_factory=dict)


class MetabaseEmbedSpec(BaseModel):
    resource_type: str  # dashboard|question
    resource_id: int
    params: Dict[str, Any] = Field(default_factory=dict)
    theme: str = "light"


# Report Builder
class ReportSheetSpec(BaseModel):
    name: str
    source: str  # metabase_card | mongo
    metabase_card_id: Optional[int] = None
    metabase_params: Dict[str, Any] = Field(default_factory=dict)
    mongo_collection: Optional[str] = None
    mongo_pipeline: List[Dict[str, Any]] = Field(default_factory=list)


class ReportSpec(BaseModel):
    title: str
    sheets: List[ReportSheetSpec]


# Planning
class ToolCall(BaseModel):
    tool: str  # mongo.read | df.op | plot | excel | crm.* | metabase.query | metabase.embed | report.build
    args: Dict[str, Any]


class Plan(BaseModel):
    intent: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    final_message: Optional[str] = None


# Frontend Models/DTOs
class KPIResponse(BaseModel):
    mtd_revenue: Dict[str, Any]
    new_leads: Dict[str, Any]
    win_rate: Dict[str, Any]
    avg_cycle: Dict[str, Any]


class DataExplorerRequest(BaseModel):
    collection: str = "leads"
    filters: Dict[str, Any] = Field(default_factory=dict)
    search: Optional[str] = None
    page: int = 1
    limit: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class DataExplorerResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    has_more: bool


class SavedReport(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    spec: ReportSpec
    schedule: Optional[str] = None
    status: str = "draft"
    created_by: str
    created_at: Optional[str] = None
    last_run: Optional[str] = None


class ReportListResponse(BaseModel):
    reports: List[SavedReport]


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    message_count: int


class ChatResponse(BaseModel):
    message: str
    preview_rows: List[Dict[str, Any]] = []
    artifacts: Dict[str, Any] = {}
    embed_urls: List[str] = []
    plan: Dict[str, Any]
    schema_catalog: Dict[str, Any]
    timestamp: str


