"""
CRM Agent – conversational, analytics + Metabase integration (single-file)

What you get
------------
• FastAPI server with a /chat endpoint that runs a plan–act–observe loop and keeps **conversational state** per session.
• Read tools for MongoDB (leads, tasks, notes, call_logs, activity) with guardrails + RBAC.
• DataFrame ops, Excel export, and Matplotlib plots.
• **Metabase integration**
    - Signed **embed URLs** for dashboards/questions (JWT signed embedding).
    - Query **cards (questions)** via API and pull results as DataFrames for Excel/plots.
• **Report Builder**: multi-sheet Excel reports from Mongo + Metabase cards via a single spec.
• Swagger/OpenAPI-backed write actions: create task, note, call log, activity; update lead.
• Artifact store for downloadable XLSX/PNG; embed URL list for frontends.

Quick start
-----------
1) pip install -r requirements.txt  (see REQUIREMENTS)
2) Set env vars (.env works). See CONFIG below.
3) uvicorn crm_agent_full:app --reload
4) POST /chat with {"session_id":"demo","user_id":"alice","message":"Build a pipeline by owner report and share a chart"}

REQUIREMENTS (pip)
------------------
fastapi
uvicorn
pydantic>=2
pandas
matplotlib
pymongo
python-dotenv
PyYAML
requests
openapi-schema-pydantic
xlsxwriter
PyJWT

CONFIG (env / .env)
-------------------
MONGO_URI=mongodb://localhost:27017
MONGO_DB=crm
ALLOWED_COLLECTIONS=leads,tasks,notes,call_logs,activity

# Swagger/OpenAPI backend (replace with your CRM details)
SWAGGER_SPEC_URL=https://your-crm.example.com/swagger/v1/swagger.json
SWAGGER_BASE_URL=https://your-crm.example.com
SWAGGER_AUTH_HEADER=Authorization
SWAGGER_AUTH_VALUE=Bearer YOUR_TOKEN

# LLM (swap for your provider or Groq)
LLM_PROVIDER=json_stub  # json_stub|openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini

# Metabase
METABASE_SITE_URL=https://metabase.example.com
METABASE_USERNAME=me@example.com           # optional if using session token
METABASE_PASSWORD=********                 # optional if using session token
METABASE_SESSION_TOKEN=                    # if provided, used directly
METABASE_EMBED_SECRET=super-secret-string  # for signed embedding

Notes
-----
• Self-contained for clarity; in production, split into modules and add persistent stores.
• LLM client shows a **JSON-only** interface; swap with your model (OpenAI, Groq) that returns a Plan JSON.
• Metabase: we support both **signed embed URLs** and **card query via API**; adjust endpoints as needed for your MB version.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
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
from dataclasses import dataclass
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

mongo_client = MongoClient(CFG.MONGO_URI)
ctx = ToolContext(mongo_client, CFG.MONGO_DB)

# ------------------------- Swagger Client --------------------
class SwaggerClient:
    def __init__(self, base_url: str, spec_url: str, auth_header: Optional[str]=None, auth_value: Optional[str]=None):
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

    def call(self, *, path: Optional[str]=None, method: Optional[str]=None, operation_id: Optional[str]=None,
             path_params: Optional[Dict[str, Any]]=None, query: Optional[Dict[str, Any]]=None,
             body: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        if operation_id and not (path and method):
            path, method = self._resolve_operation_id(operation_id)
        if not path or not method:
            raise ValueError("Provide either (operation_id) or (path & method)")
        url = self._format_path(path, path_params or {})
        req_headers = {}
        if headers: req_headers.update(headers)
        url = f"{self.base_url}{url}"
        m = method.upper()
        data = json.dumps(body) if body is not None else None
        resp = self.session.request(m, url, params=query, data=data, headers={**req_headers, "Content-Type":"application/json"}, timeout=30)
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
            path = path.replace("{"+k+"}", str(v))
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

    def query_card_json(self, card_id: int, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
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

    def query_card_dataframe(self, card_id: int, params: Optional[Dict[str, Any]]=None) -> pd.DataFrame:
        data = self.query_card_json(card_id, params)
        # Metabase returns {data: {rows: [...], cols: [{name:..}]}} or a similar structure
        d = data.get("data") or data
        rows = d.get("rows", [])
        cols = [c.get("name") for c in d.get("cols", [])]
        if rows and cols:
            return pd.DataFrame(rows, columns=cols)
        # Fallback: try results array
        if isinstance(d, dict) and "results" in d and isinstance(d["results"], list):
            return pd.DataFrame(d["results"])
        return pd.DataFrame(rows)

    def signed_embed_url(self, resource_type: str, resource_id: int, params: Optional[Dict[str, Any]]=None, theme: str="light", expires_minutes: int=60) -> str:
        if not self.embed_secret or not self.site:
            raise HTTPException(status_code=503, detail="Metabase embed secret or site URL not configured")
        assert resource_type in {"dashboard", "question"}
        payload = {
            "resource": {resource_type: resource_id},
            "params": params or {},
            "exp": int((datetime.utcnow() + timedelta(minutes=expires_minutes)).timestamp())
        }
        token = jwt.encode(payload, self.embed_secret, algorithm="HS256")
        path = "/embed/dashboard/" if resource_type == "dashboard" else "/embed/question/"
        # theme/border can be query params per Metabase embedding docs
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
    due_date: Optional[str] = None  # ISO date
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
    when: Optional[str] = None  # ISO datetime
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
        pv = pd.pivot_table(df, index=p["index"], columns=p["columns"], values=p["values"], aggfunc=p.get("aggfunc","sum"))
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

# Minimal JSON-only LLM client
class LLMClient:
    def __init__(self):
        self.provider = CFG.LLM_PROVIDER
        self.model = CFG.OPENAI_MODEL
        self.api_key = CFG.OPENAI_API_KEY

    def plan(self, system: str, messages: List[Dict[str, str]], tools_schema: Dict[str, Any]) -> Plan:
        user_msg = messages[-1]["content"].lower()
        # Heuristic flows to keep this file runnable without external LLMs
        if "metabase" in user_msg and ("embed" in user_msg or "dashboard" in user_msg or "question" in user_msg):
            plan = {
                "intent": "metabase_embed",
                "tool_calls": [
                    {"tool":"metabase.embed","args":{"resource_type":"dashboard","resource_id":1,"params":{},"theme":"light"}}
                ],
                "final_message": "Generated an embed URL for your Metabase dashboard."
            }
            return Plan(**plan)
        if "report" in user_msg and "build" in user_msg:
            plan = {
                "intent": "report_build",
                "tool_calls": [
                    {"tool":"metabase.query","args":{"card_id":1,"params":{}}},
                    {"tool":"df.op","args":{"operation":"groupby","params":{"by":["owner"],"agg":{"amount":"sum"}}}},
                    {"tool":"excel","args":{"sheet_name":"Summary","index":False,"autofit":True}}
                ],
                "final_message": "Built a simple report and exported Excel."
            }
            return Plan(**plan)
        if "export" in user_msg and "excel" in user_msg:
            plan = {
                "intent": "analytics_export",
                "tool_calls": [
                    {"tool":"mongo.read","args":{"collection":"leads","pipeline":[],"limit":5000}},
                    {"tool":"df.op","args":{"operation":"groupby","params":{"by":["owner"],"agg":{"amount":"sum"}}}},
                    {"tool":"excel","args":{"sheet_name":"Report","index":False,"autofit":True}}
                ],
                "final_message": "Exported Excel with totals by owner."
            }
            return Plan(**plan)
        # Fallback: do-nothing until you wire a real model
        if CFG.LLM_PROVIDER == "json_stub":
            return Plan(intent="noop", tool_calls=[], final_message="No tools executed. Configure LLM_PROVIDER or refine your prompt.")
        elif CFG.LLM_PROVIDER == "openai":
            import openai  # type: ignore
            openai.api_key = self.api_key
            sys = {"role":"system","content": system}
            msgs = [sys] + messages + [{"role":"system","content": "Return ONLY a JSON object matching the Plan model."}]
            prompt = json.dumps({"tools_schema": tools_schema, "messages": msgs})
            resp = openai.chat.completions.create(model=self.model, messages=[{"role":"user","content": prompt}], temperature=0)
            text = resp.choices[0].message.content
            try:
                return Plan(**json.loads(text))
            except Exception as e:
                logger.error(f"LLM parse error: {e}; text={text}")
                raise HTTPException(status_code=500, detail="LLM returned invalid plan JSON")
        else:
            raise HTTPException(status_code=500, detail="Unsupported LLM_PROVIDER.")

# Human-readable schema catalog for grounding

def build_schema_catalog() -> Dict[str, Any]:
    catalog = {}
    for name in CFG.ALLOWED_COLLECTIONS:
        try:
            sample = ctx.db[name].find_one()
            if not sample:
                fields = []
            else:
                fields = sorted(sample.keys())
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

# ------------------------- FastAPI ---------------------------
app = FastAPI(title="CRM Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

class ChatResponse(BaseModel):
    message: str
    preview_rows: List[Dict[str, Any]] = []
    artifacts: Dict[str, Any] = {}
    embed_urls: List[str] = []
    plan: Dict[str, Any]
    schema_catalog: Dict[str, Any]
    timestamp: str

# Report Builder tool execution

def build_report(user_id: str, spec: ReportSpec) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # cover sheet
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
            # autofit
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
                art_id = save_artifact(xlsx, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="report.xlsx")
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
                art_id = save_artifact(xlsx, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"{spec.title}.xlsx")
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

@app.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str):
    item = ARTIFACTS.get(artifact_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return StreamingResponse(io.BytesIO(item["bytes"]), media_type=item["mime"], headers={"Content-Disposition": f"attachment; filename={item['filename']}"})

class PlanOnlyRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

@app.post("/plan")
def plan_only(req: PlanOnlyRequest):
    schema_catalog = build_schema_catalog()
    history = MEMORY.get(req.session_id)
    messages = history + [{"role":"user","content": req.message}]
    plan = client.plan(
        system=(SYSTEM_PROMPT + f"\nSchema catalog: {json.dumps(schema_catalog)[:2000]}"),
        messages=messages,
        tools_schema=TOOLS_SCHEMA,
    )
    return {"plan": plan.model_dump()}

@app.post("/chat")
def chat(req: ChatRequest):
    schema_catalog = build_schema_catalog()
    history = MEMORY.get(req.session_id)
    history.append({"role":"user","content": req.message})

    plan = client.plan(
        system=(SYSTEM_PROMPT + f"\nSchema catalog: {json.dumps(schema_catalog)[:2000]}"),
        messages=history,
        tools_schema=TOOLS_SCHEMA,
    )
    result = execute_plan(req.session_id, req.user_id, plan)

    # Save assistant reply to memory
    MEMORY.append(req.session_id, "assistant", result.get("message", ""))

    return {
        "message": result.get("message", ""),
        "preview_rows": result.get("preview_rows", []),
        "artifacts": result.get("artifacts", {}),
        "embed_urls": result.get("embed_urls", []),
        "plan": plan.model_dump(),
        "schema_catalog": schema_catalog,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ------------------------- Health & Info ---------------------
@app.get("/")
def root():
    return {"message": "CRM Agent API", "version": "1.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/info")
def info():
    return {
        "collections": list(CFG.ALLOWED_COLLECTIONS),
        "metabase_configured": bool(CFG.METABASE_SITE_URL),
        "swagger_configured": bool(CFG.SWAGGER_BASE_URL),
        "llm_provider": CFG.LLM_PROVIDER,
    }

# ------------------------- Example Prompts -------------------
"""
Examples
--------
1) Conversational analytics with Metabase embed
   {"session_id":"s1","user_id":"alice","message":"Show me the sales performance dashboard from Metabase as an embed."}

2) Report builder using Metabase card + Mongo sheet
   {"session_id":"s1","user_id":"alice","message":"Build a weekly pipeline report"}
   (with a real LLM, craft a plan that calls report.build like)
   {
     "tool":"report.build",
     "args":{
       "title":"Weekly Pipeline",
       "sheets":[
         {"name":"By Owner","source":"metabase_card","metabase_card_id":123,"metabase_params":{}},
         {"name":"Stale Leads","source":"mongo","mongo_collection":"leads","mongo_pipeline":[{"$match":{"status":"Contacted"}}]}
       ]
     }
   }

3) Write actions from conversation
   "Create follow-up tasks due Friday for leads with no activity in 14 days"
   -> plan uses mongo.read + df.op(filter) then crm.create_task in a loop (batch in your orchestration if needed).
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
