from __future__ import annotations

from typing import Any, Dict

from .planning import LLMClient
from .schema import build_schema_catalog
from .memory import MEMORY


client = LLMClient()


SYSTEM_PROMPT = (
    "You are a conversational CRM agent. Maintain context across messages. You have tools to read MongoDB collections (leads, tasks, notes, call_logs, activity), "
    "perform DataFrame operations, export Excel, make charts, query/ embed Metabase, and create CRM records via swagger-backed endpoints. "
    "Plan a sequence of tool calls to satisfy the user's request, keep row limits reasonable, prefer aggregations, and return a JSON Plan."
)


def plan_only_logic(session_id: str, user_id: str, message: str) -> Dict[str, Any]:
    schema_catalog = build_schema_catalog()
    history = MEMORY.get(session_id)
    messages = history + [{"role": "user", "content": message}]
    plan = client.plan(
        system=(SYSTEM_PROMPT + f"\nSchema catalog: {__import__('json').dumps(schema_catalog)[:2000]}"),
        messages=messages,
        tools_schema=TOOLS_SCHEMA,
    )
    return {"plan": plan.model_dump()}


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
    MetabaseQuerySpec,
    MetabaseEmbedSpec,
)

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

