from __future__ import annotations

# Thin compatibility facade re-exporting public API from granular modules

from typing import Any, Dict
from datetime import datetime, timezone
import json

from .config import CFG, logger
from .rbac import rbac_policy
from .db import ctx, MONGO_AVAILABLE, MOCK_DATA
from .metabase_client import metabase
from .models import (
    MongoReadSpec,
    DataframeOpSpec,
    PlotSpec,
    ExcelSpec,
    CreateTaskSpec,
    CreateNoteSpec,
    LogCallSpec,
    CreateActivitySpec,
    UpdateLeadSpec,
    ReportSheetSpec,
    ReportSpec,
    KPIResponse,
    DataExplorerRequest,
    DataExplorerResponse,
    SavedReport,
    ReportListResponse,
    SessionInfo,
)
from .tools import run_mongo, dataframe_ops, make_plot, export_excel, metabase_query_df, metabase_embed_url
from .executor import execute_plan, create_task, create_note, log_call, create_activity, update_lead
from .storage import save_artifact, ARTIFACTS
from .schema import build_schema_catalog
from .planning import LLMClient
from .plan_api import TOOLS_SCHEMA, SYSTEM_PROMPT
from .memory import MEMORY, SESSION_METADATA
from .reports import build_report
from .services import (
    calc_kpis,
    explore_data_logic,
    export_collection_logic,
    list_reports_logic,
    create_report_logic,
    get_report_logic,
    run_report_logic,
    delete_report_logic,
    get_artifact_bytes,
    list_artifacts_logic,
    get_collection_schema_logic,
)
from .defaults import initialize_default_reports


client = LLMClient()
initialize_default_reports()

