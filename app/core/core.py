from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import os
import io
import json
import base64
import logging
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import requests
import jwt


# ------------------------- Bootstrap -------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crm_agent")


# ------------------------- Config ----------------------------
@dataclass
class Config:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "crm")
    ALLOWED_COLLECTIONS: List[str] = tuple(os.getenv("ALLOWED_COLLECTIONS", "leads,tasks,notes,call_logs,activity").split(","))

    SWAGGER_SPEC_URL: Optional[str] = os.getenv("SWAGGER_SPEC_URL")
    SWAGGER_BASE_URL: Optional[str] = os.getenv("SWAGGER_BASE_URL")
    SWAGGER_AUTH_HEADER: Optional[str] = os.getenv("SWAGGER_AUTH_HEADER")
    SWAGGER_AUTH_VALUE: Optional[str] = os.getenv("SWAGGER_AUTH_VALUE")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "json_stub")  # json_stub|openai
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    METABASE_SITE_URL: Optional[str] = os.getenv("METABASE_SITE_URL")
    METABASE_USERNAME: Optional[str] = os.getenv("METABASE_USERNAME")
    METABASE_PASSWORD: Optional[str] = os.getenv("METABASE_PASSWORD")
    METABASE_SESSION_TOKEN: Optional[str] = os.getenv("METABASE_SESSION_TOKEN")
    METABASE_EMBED_SECRET: Optional[str] = os.getenv("METABASE_EMBED_SECRET")


CFG = Config()


# ------------------------- RBAC ------------------------------
def rbac_policy(user_id: str) -> Dict[str, Any]:
    return {
        "allow_collections": list(CFG.ALLOWED_COLLECTIONS),
        "deny_fields": ["ssn", "salary"],
        "role": "admin" if user_id in {"admin", "alice"} else "analyst",
    }


# ------------------------- Mongo Context ---------------------
class ToolContext:
    def __init__(self, mongo_client: MongoClient, db_name: str):
        self.client = mongo_client
        self.db = mongo_client[db_name]


try:
    mongo_client = MongoClient(CFG.MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    ctx = ToolContext(mongo_client, CFG.MONGO_DB)
    MONGO_AVAILABLE = True
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"⚠️ MongoDB not available: {e}")
    print("🔄 Using mock data for demonstration")
    mongo_client = None
    ctx = None
    MONGO_AVAILABLE = False


# ------------------------- Swagger Client --------------------
class SwaggerClient:
    def __init__(self, base_url: str, spec_url: str, auth_header: Optional[str] = None, auth_value: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.spec_url = spec_url
        self.session = requests.Session()
        if auth_header and auth_value:
            self.session.headers[auth_header] = auth_value
        self.spec: Dict[str, Any] = {}
        try:
            self._load_spec()
        except Exception as e:
            logger.warning(f"Unable to load OpenAPI spec at startup: {e}")

    def _load_spec(self):
        resp = self.session.get(self.spec_url, timeout=20)
        resp.raise_for_status()
        self.spec = resp.json()

    def call(
        self,
        *,
        path: Optional[str] = None,
        method: Optional[str] = None,
        operation_id: Optional[str] = None,
        path_params: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if operation_id and not (path and method):
            path, method = self._resolve_operation_id(operation_id)
        if not path or not method:
            raise ValueError("Provide either (operation_id) or (path & method)")
        url = self._format_path(path, path_params or {})
        req_headers = {}
        if headers:
            req_headers.update(headers)
        url = f"{self.base_url}{url}"
        m = method.upper()
        data = json.dumps(body) if body is not None else None
        resp = self.session.request(
            m,
            url,
            params=query,
            data=data,
            headers={**req_headers, "Content-Type": "application/json"},
            timeout=30,
        )
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        try:
            return resp.json()
        except Exception:
            return {"text": resp.text}

    def _resolve_operation_id(self, operation_id: str) -> Tuple[str, str]:
        paths = self.spec.get("paths", {})
        for p, methods in paths.items():
            for m, op in methods.items():
                if isinstance(op, dict) and op.get("operationId") == operation_id:
                    return p, m
        raise ValueError(f"operationId '{operation_id}' not found in spec")

    @staticmethod
    def _format_path(path: str, params: Dict[str, Any]) -> str:
        for k, v in params.items():
            path = path.replace("{" + k + "}", str(v))
        return path


swagger: Optional[SwaggerClient] = None
if CFG.SWAGGER_BASE_URL and CFG.SWAGGER_SPEC_URL:
    swagger = SwaggerClient(
        base_url=CFG.SWAGGER_BASE_URL,
        spec_url=CFG.SWAGGER_SPEC_URL,
        auth_header=CFG.SWAGGER_AUTH_HEADER,
        auth_value=CFG.SWAGGER_AUTH_VALUE,
    )


# ------------------------- Metabase Client -------------------
class MetabaseClient:
    def __init__(self):
        self.site = (CFG.METABASE_SITE_URL or "").rstrip("/")
        self.session = requests.Session()
        self.session_token = CFG.METABASE_SESSION_TOKEN
        if not self.session_token and CFG.METABASE_USERNAME and CFG.METABASE_PASSWORD and self.site:
            try:
                self.login(CFG.METABASE_USERNAME, CFG.METABASE_PASSWORD)
            except Exception as e:
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


# ------------------------- Tool Schemas ----------------------
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


# ------------------------- Tool Implementations --------------
def _enforce_rbac_collection(user_id: str, collection: str):
    policy = rbac_policy(user_id)
    if collection not in policy["allow_collections"]:
        raise HTTPException(status_code=403, detail=f"User not allowed to access collection {collection}")


def run_mongo(user_id: str, spec: MongoReadSpec) -> pd.DataFrame:
    _enforce_rbac_collection(user_id, spec.collection)

    if not MONGO_AVAILABLE:
        mock_rows = MOCK_DATA.get(spec.collection, [])
        if not mock_rows:
            return pd.DataFrame()
        df = pd.json_normalize(mock_rows)
        if spec.limit:
            df = df.head(spec.limit)
        deny = set(rbac_policy(user_id).get("deny_fields", []))
        keep = [c for c in df.columns if c.split(".")[0] not in deny]
        return df[keep]

    for stage in spec.pipeline:
        if "$where" in stage or "$function" in stage:
            raise HTTPException(status_code=400, detail="Forbidden stage in pipeline")
    try:
        cursor = ctx.db[spec.collection].aggregate(spec.pipeline + [{"$limit": spec.limit}])
        rows = list(cursor)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not rows:
        return pd.DataFrame()
    df = pd.json_normalize(rows)
    deny = set(rbac_policy(user_id).get("deny_fields", []))
    keep = [c for c in df.columns if c.split(".")[0] not in deny]
    return df[keep]


def dataframe_ops(df: pd.DataFrame, spec: DataframeOpSpec) -> pd.DataFrame:
    op = spec.operation.lower()
    p = spec.params
    if df is None:
        return pd.DataFrame()
    if op == "select":
        return df[p["columns"]]
    if op == "filter":
        return df.query(p["query"])  # e.g., "status == 'Open' and amount > 10000"
    if op == "sort":
        return df.sort_values(by=p["by"], ascending=p.get("ascending", True))
    if op == "groupby":
        grp = df.groupby(p["by"])
        agg = grp.agg(p.get("agg", {p.get("value_col", "_id"): "count"})).reset_index()
        return agg
    if op == "pivot":
        pv = pd.pivot_table(
            df,
            index=p["index"],
            columns=p["columns"],
            values=p["values"],
            aggfunc=p.get("aggfunc", "sum"),
        )
        return pv.reset_index()
    raise HTTPException(status_code=400, detail=f"Unknown operation {op}")


def make_plot(df: pd.DataFrame, spec: PlotSpec) -> bytes:
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="No data to plot")
    if spec.kind in ("bar", "line") and spec.x and spec.y:
        series = df.groupby(spec.x)[spec.y].sum()
        ax = series.plot(kind=spec.kind)
    elif spec.kind == "pie" and spec.y:
        ax = df[spec.y].value_counts().plot(kind="pie")
    elif spec.kind == "scatter" and spec.x and spec.y:
        ax = df.plot(kind="scatter", x=spec.x, y=spec.y)
    else:
        raise HTTPException(status_code=400, detail="Invalid plot spec for the provided DataFrame")
    if spec.title:
        ax.set_title(spec.title)
    fig = ax.get_figure()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def export_excel(df: pd.DataFrame, spec: ExcelSpec) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=spec.sheet_name, index=spec.index)
        if spec.autofit:
            ws = writer.sheets[spec.sheet_name]
            for i, col in enumerate(df.columns, start=1):
                safe = df[col].astype(str)
                width = max(10, min(60, int(safe.str.len().quantile(0.9)) + 3))
                ws.set_column(i, i, width)
    return buf.getvalue()


# ---- Metabase adapters ----
def metabase_query_df(spec: MetabaseQuerySpec) -> pd.DataFrame:
    return metabase.query_card_dataframe(spec.card_id, spec.params)


def metabase_embed_url(spec: MetabaseEmbedSpec) -> str:
    return metabase.signed_embed_url(spec.resource_type, spec.resource_id, spec.params, theme=spec.theme)


# ---- Write tool adapters via Swagger ----
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


# ------------------------- Conversation State ----------------
class ChatMemory:
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

    def get(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions.setdefault(session_id, [])

    def append(self, session_id: str, role: str, content: str):
        self.sessions.setdefault(session_id, []).append({"role": role, "content": content})


MEMORY = ChatMemory()


# ------------------------- Plans & Controller ----------------
class ToolCall(BaseModel):
    tool: str  # mongo.read | df.op | plot | excel | crm.* | metabase.query | metabase.embed | report.build
    args: Dict[str, Any]


class Plan(BaseModel):
    intent: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    final_message: Optional[str] = None


class LLMClient:
    def __init__(self):
        self.provider = CFG.LLM_PROVIDER
        self.model = CFG.OPENAI_MODEL
        self.api_key = CFG.OPENAI_API_KEY

    def plan(self, system: str, messages: List[Dict[str, str]], tools_schema: Dict[str, Any]) -> Plan:
        user_msg = messages[-1]["content"].lower()

        if "deals created last week" in user_msg and "owner" in user_msg and "chart" in user_msg:
            plan = {
                "intent": "weekly_deals_chart",
                "tool_calls": [
                    {
                        "tool": "mongo.read",
                        "args": {
                            "collection": "leads",
                            "pipeline": [
                                {"$match": {"created_date": {"$gte": (datetime.now() - timedelta(days=7)).isoformat()}}},
                                {"$group": {"_id": "$owner", "count": {"$sum": 1}}},
                            ],
                            "limit": 1000,
                        },
                    },
                    {"tool": "plot", "args": {"kind": "bar", "x": "_id", "y": "count", "title": "Deals Created Last Week by Owner"}},
                ],
                "final_message": "Generated a bar chart showing deals created last week by owner.",
            }
            return Plan(**plan)

        if "leads with no activity" in user_msg and "14 days" in user_msg:
            plan = {
                "intent": "stale_leads_analysis",
                "tool_calls": [
                    {
                        "tool": "mongo.read",
                        "args": {
                            "collection": "leads",
                            "pipeline": [
                                {"$lookup": {"from": "activity", "localField": "_id", "foreignField": "lead_id", "as": "activities"}},
                                {"$match": {"$or": [{"activities": {"$size": 0}}, {"activities.when": {"$lt": (datetime.now() - timedelta(days=14)).isoformat()}}]}},
                                {"$project": {"name": 1, "company": 1, "owner": 1, "status": 1, "amount": 1, "created_date": 1}},
                            ],
                            "limit": 5000,
                        },
                    },
                    {"tool": "excel", "args": {"sheet_name": "Stale_Leads", "index": False, "autofit": True}},
                ],
                "final_message": "Exported leads with no activity in the last 14 days to Excel.",
            }
            return Plan(**plan)

        if "mtd revenue" in user_msg and ("target" in user_msg or "region" in user_msg):
            plan = {
                "intent": "mtd_revenue_analysis",
                "tool_calls": [
                    {
                        "tool": "mongo.read",
                        "args": {
                            "collection": "leads",
                            "pipeline": [
                                {"$match": {"created_date": {"$gte": datetime.now().replace(day=1).isoformat()}, "status": "Won"}},
                                {"$group": {"_id": "$region", "revenue": {"$sum": "$amount"}}},
                            ],
                            "limit": 1000,
                        },
                    },
                    {"tool": "plot", "args": {"kind": "bar", "x": "_id", "y": "revenue", "title": "MTD Revenue by Region"}},
                ],
                "final_message": "Generated MTD revenue analysis by region.",
            }
            return Plan(**plan)

        if "pipeline forecast" in user_msg or "next quarter" in user_msg:
            plan = {
                "intent": "pipeline_forecast",
                "tool_calls": [
                    {
                        "tool": "mongo.read",
                        "args": {
                            "collection": "leads",
                            "pipeline": [
                                {"$match": {"status": {"$in": ["Qualified", "Proposal", "Negotiation"]}}},
                                {"$group": {"_id": "$status", "total_amount": {"$sum": "$amount"}, "count": {"$sum": 1}}},
                            ],
                            "limit": 1000,
                        },
                    },
                    {"tool": "plot", "args": {"kind": "bar", "x": "_id", "y": "total_amount", "title": "Pipeline Forecast by Stage"}},
                ],
                "final_message": "Generated pipeline forecast for next quarter.",
            }
            return Plan(**plan)

        if "metabase" in user_msg and ("embed" in user_msg or "dashboard" in user_msg or "question" in user_msg):
            plan = {
                "intent": "metabase_embed",
                "tool_calls": [
                    {"tool": "metabase.embed", "args": {"resource_type": "dashboard", "resource_id": 1, "params": {}, "theme": "light"}},
                ],
                "final_message": "Generated an embed URL for your Metabase dashboard.",
            }
            return Plan(**plan)

        if "report" in user_msg and "build" in user_msg:
            plan = {
                "intent": "report_build",
                "tool_calls": [
                    {"tool": "metabase.query", "args": {"card_id": 1, "params": {}}},
                    {"tool": "df.op", "args": {"operation": "groupby", "params": {"by": ["owner"], "agg": {"amount": "sum"}}}},
                    {"tool": "excel", "args": {"sheet_name": "Summary", "index": False, "autofit": True}},
                ],
                "final_message": "Built a simple report and exported Excel.",
            }
            return Plan(**plan)

        if "export" in user_msg and "excel" in user_msg:
            plan = {
                "intent": "analytics_export",
                "tool_calls": [
                    {"tool": "mongo.read", "args": {"collection": "leads", "pipeline": [], "limit": 5000}},
                    {"tool": "df.op", "args": {"operation": "groupby", "params": {"by": ["owner"], "agg": {"amount": "sum"}}}},
                    {"tool": "excel", "args": {"sheet_name": "Report", "index": False, "autofit": True}},
                ],
                "final_message": "Exported Excel with totals by owner.",
            }
            return Plan(**plan)

        if CFG.LLM_PROVIDER == "json_stub":
            return Plan(intent="noop", tool_calls=[], final_message="No tools executed. Configure LLM_PROVIDER or refine your prompt.")
        elif CFG.LLM_PROVIDER == "openai":
            import openai  # type: ignore

            openai.api_key = self.api_key
            sys = {"role": "system", "content": system}
            msgs = [sys] + messages + [{"role": "system", "content": "Return ONLY a JSON object matching the Plan model."}]
            prompt = json.dumps({"tools_schema": tools_schema, "messages": msgs})
            resp = openai.chat.completions.create(model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0)
            text = resp.choices[0].message.content
            try:
                return Plan(**json.loads(text))
            except Exception as e:
                logger.error(f"LLM parse error: {e}; text={text}")
                raise HTTPException(status_code=500, detail="LLM returned invalid plan JSON")
        else:
            raise HTTPException(status_code=500, detail="Unsupported LLM_PROVIDER.")


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


TOOLS_SCHEMA = {
    "mongo.read": MongoReadSpec.model_json_schema(),
    "df.op": DataframeOpSpec.model_json_schema(),
    "plot": PlotSpec.model_json_schema(),
    "excel": ExcelSpec.model_json_schema(),
    "crm.create_task": CreateTaskSpec.model_json_schema(),
    "crm.create_note": CreateNoteSpec.model_json_schema(),
    "crm.log_call": LogCallSpec.model_json_schema(),
    "crm.create_activity": CreateActivitySpec.model_json_schema(),
    "crm.update_lead": UpdateLeadSpec.model_json_schema(),
    "metabase.query": MetabaseQuerySpec.model_json_schema(),
    "metabase.embed": MetabaseEmbedSpec.model_json_schema(),
}


SYSTEM_PROMPT = (
    "You are a conversational CRM agent. Maintain context across messages. You have tools to read MongoDB collections (leads, tasks, notes, call_logs, activity), "
    "perform DataFrame operations, export Excel, make charts, query/ embed Metabase, and create CRM records via swagger-backed endpoints. "
    "Plan a sequence of tool calls to satisfy the user's request, keep row limits reasonable, prefer aggregations, and return a JSON Plan."
)


client = LLMClient()


# ------------------------- Artifact store --------------------
ARTIFACTS: Dict[str, Dict[str, Any]] = {}


def save_artifact(payload: bytes, *, mime: str, filename: str) -> str:
    artifact_id = base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("=")
    ARTIFACTS[artifact_id] = {"bytes": payload, "mime": mime, "filename": filename}
    return artifact_id


# ------------------------- Report Builder --------------------
def build_report(user_id: str, spec: ReportSpec) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        meta = pd.DataFrame([[spec.title, datetime.now(timezone.utc).isoformat()]], columns=["title", "generated_at"])
        meta.to_excel(writer, sheet_name="_meta", index=False)
        for sheet in spec.sheets:
            if sheet.source == "metabase_card" and sheet.metabase_card_id is not None:
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
            elif tc.tool == "report.build":
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
            logger.exception("Tool execution error")
            raise HTTPException(status_code=500, detail=f"Tool execution error in {tc.tool}: {e}")

    response["message"] = plan.final_message or "Done."
    response["audit"] = audit
    return response


# ------------------------- Frontend Models/DTOs --------------
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


# ------------------------- In-Memory Storage -----------------
SAVED_REPORTS: Dict[str, SavedReport] = {}
SESSION_METADATA: Dict[str, Dict[str, Any]] = {}


MOCK_DATA = {
    "leads": [
        {
            "_id": "lead_001",
            "name": "Acme Corp Renewal",
            "company": "Acme Corporation",
            "email": "contact@acme.com",
            "owner": "Priya",
            "status": "Proposal",
            "amount": 24000,
            "source": "Referral",
            "region": "North",
            "created_date": (datetime.now() - timedelta(days=45)).isoformat(),
        },
        {
            "_id": "lead_002",
            "name": "Globex Expansion",
            "company": "Globex Industries",
            "email": "sales@globex.com",
            "owner": "Aryan",
            "status": "Qualified",
            "amount": 85000,
            "source": "Website",
            "region": "South",
            "created_date": (datetime.now() - timedelta(days=30)).isoformat(),
        },
        {
            "_id": "lead_003",
            "name": "TechCorp Integration",
            "company": "TechCorp Solutions",
            "email": "info@techcorp.com",
            "owner": "Sneha",
            "status": "Discovery",
            "amount": 45000,
            "source": "Cold Outreach",
            "region": "West",
            "created_date": (datetime.now() - timedelta(days=15)).isoformat(),
        },
        {
            "_id": "lead_004",
            "name": "StartupXYZ Deal",
            "company": "StartupXYZ",
            "email": "founder@startupxyz.com",
            "owner": "Priya",
            "status": "Won",
            "amount": 35000,
            "source": "Referral",
            "region": "North",
            "created_date": (datetime.now() - timedelta(days=60)).isoformat(),
        },
    ],
    "tasks": [
        {
            "_id": "task_001",
            "title": "Follow up with Acme Corp",
            "lead_id": "lead_001",
            "owner_id": "Priya",
            "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "priority": "High",
            "status": "Open",
        }
    ],
    "activity": [
        {
            "_id": "activity_001",
            "lead_id": "lead_001",
            "type": "email",
            "when": (datetime.now() - timedelta(days=2)).isoformat(),
            "notes": "Sent proposal document",
            "created_by": "Priya",
        }
    ],
    "notes": [
        {
            "_id": "note_001",
            "lead_id": "lead_001",
            "body": "Client interested in annual contract",
            "created_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "created_by": "Priya",
        }
    ],
}


def initialize_default_reports():
    default_reports = [
        SavedReport(
            id="weekly-pipeline",
            name="Weekly Pipeline Summary",
            description="Deals by stage with weekly trends",
            spec=ReportSpec(
                title="Weekly Pipeline Summary",
                sheets=[
                    ReportSheetSpec(
                        name="By Stage",
                        source="mongo",
                        mongo_collection="leads",
                        mongo_pipeline=[{"$group": {"_id": "$status", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}}],
                    ),
                    ReportSheetSpec(
                        name="By Owner",
                        source="mongo",
                        mongo_collection="leads",
                        mongo_pipeline=[{"$group": {"_id": "$owner", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}}],
                    ),
                ],
            ),
            schedule="Weekly (Monday 9:00 IST)",
            status="active",
            created_by="system",
            created_at=datetime.now(timezone.utc).isoformat(),
            last_run="2025-08-25",
        ),
        SavedReport(
            id="mtd-revenue",
            name="MTD Revenue Analysis",
            description="Revenue breakdown by source and owner",
            spec=ReportSpec(
                title="MTD Revenue Analysis",
                sheets=[
                    ReportSheetSpec(
                        name="Revenue by Source",
                        source="mongo",
                        mongo_collection="leads",
                        mongo_pipeline=[
                            {"$match": {"status": "Won", "created_date": {"$gte": datetime.now().replace(day=1).isoformat()}}},
                            {"$group": {"_id": "$source", "revenue": {"$sum": "$amount"}}},
                        ],
                    )
                ],
            ),
            schedule="Monthly (1st, 9:00 IST)",
            status="active",
            created_by="system",
            created_at=datetime.now(timezone.utc).isoformat(),
            last_run="2025-08-20",
        ),
        SavedReport(
            id="lead-activity",
            name="Lead Activity Report",
            description="Leads with no activity in 14+ days",
            spec=ReportSpec(
                title="Lead Activity Report",
                sheets=[
                    ReportSheetSpec(
                        name="Stale Leads",
                        source="mongo",
                        mongo_collection="leads",
                        mongo_pipeline=[
                            {"$lookup": {"from": "activity", "localField": "_id", "foreignField": "lead_id", "as": "activities"}},
                            {"$match": {"$or": [{"activities": {"$size": 0}}, {"activities.when": {"$lt": (datetime.now() - timedelta(days=14)).isoformat()}}]}},
                            {"$project": {"name": 1, "company": 1, "owner": 1, "status": 1, "amount": 1, "created_date": 1}},
                        ],
                    )
                ],
            ),
            schedule="None",
            status="draft",
            created_by="system",
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    ]

    for report in default_reports:
        SAVED_REPORTS[report.id] = report


initialize_default_reports()


# ------------------------- Helper APIs (logic only) ----------
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
    except Exception as e:
        logger.error(f"KPI calculation error: {e}")
        return KPIResponse(
            mtd_revenue={"value": "₹2,45,000", "change": {"value": 12.5, "type": "positive"}},
            new_leads={"value": "127", "change": {"value": 8.2, "type": "positive"}},
            win_rate={"value": "23.5%", "change": {"value": 3.1, "type": "negative"}},
            avg_cycle={"value": "18 days", "change": {"value": 5.2, "type": "positive"}},
        )


def explore_data_logic(req: DataExplorerRequest, user_id: str = "admin") -> DataExplorerResponse:
    _enforce_rbac_collection(user_id, req.collection)

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
    pipeline.extend([{"$skip": skip}, {"$limit": req.limit}])
    try:
        cursor = ctx.db[req.collection].aggregate(pipeline)
        data = list(cursor)
        deny = set(rbac_policy(user_id).get("deny_fields", []))
        if deny:
            for doc in data:
                for field in deny:
                    doc.pop(field, None)
        has_more = (skip + req.limit) < total_count
        return DataExplorerResponse(data=data, total_count=total_count, page=req.page, limit=req.limit, has_more=has_more)
    except Exception as e:
        logger.error(f"Data exploration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def export_collection_logic(collection: str, fmt: str = "excel", user_id: str = "admin") -> Dict[str, Any]:
    _enforce_rbac_collection(user_id, collection)
    try:
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
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def list_reports_logic(user_id: str = "admin") -> ReportListResponse:
    user_reports = [r for r in SAVED_REPORTS.values() if r.created_by == user_id or user_id == "admin"]
    return ReportListResponse(reports=user_reports)


def create_report_logic(report: SavedReport, user_id: str = "admin") -> SavedReport:
    report_id = base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("=")
    report.id = report_id
    report.created_by = user_id
    report.created_at = datetime.now(timezone.utc).isoformat()
    SAVED_REPORTS[report_id] = report
    return report


def get_report_logic(report_id: str, user_id: str = "admin") -> SavedReport:
    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return report


def run_report_logic(report_id: str, user_id: str = "admin") -> Dict[str, Any]:
    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        xlsx = build_report(user_id, report.spec)
        artifact_id = save_artifact(
            xlsx,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{report.name}.xlsx",
        )
        report.last_run = datetime.now(timezone.utc).isoformat()
        SAVED_REPORTS[report_id] = report
        return {"artifact_id": artifact_id, "download_url": f"/artifacts/{artifact_id}"}
    except Exception as e:
        logger.error(f"Report execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def delete_report_logic(report_id: str, user_id: str = "admin") -> Dict[str, Any]:
    report = SAVED_REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.created_by != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    del SAVED_REPORTS[report_id]
    return {"message": "Report deleted successfully"}


def list_sessions_logic(user_id: str = "admin") -> List[SessionInfo]:
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
    messages = MEMORY.get(session_id)
    metadata = SESSION_METADATA.get(session_id, {})
    if metadata.get("user_id") != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return {"session_id": session_id, "messages": messages, "metadata": metadata}


def delete_session_logic(session_id: str, user_id: str = "admin") -> Dict[str, Any]:
    metadata = SESSION_METADATA.get(session_id, {})
    if metadata.get("user_id") != user_id and user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    MEMORY.sessions.pop(session_id, None)
    SESSION_METADATA.pop(session_id, None)
    return {"message": "Session deleted successfully"}


def get_artifact_bytes(artifact_id: str) -> Dict[str, Any]:
    item = ARTIFACTS.get(artifact_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


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


def get_collection_schema_logic(collection: str, user_id: str = "admin") -> Dict[str, Any]:
    _enforce_rbac_collection(user_id, collection)
    try:
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
    except Exception as e:
        logger.error(f"Schema error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------- Planning-only helper --------------
def plan_only_logic(session_id: str, user_id: str, message: str) -> Dict[str, Any]:
    schema_catalog = build_schema_catalog()
    history = MEMORY.get(session_id)
    messages = history + [{"role": "user", "content": message}]
    plan = client.plan(
        system=(SYSTEM_PROMPT + f"\nSchema catalog: {json.dumps(schema_catalog)[:2000]}"),
        messages=messages,
        tools_schema=TOOLS_SCHEMA,
    )
    return {"plan": plan.model_dump()}

