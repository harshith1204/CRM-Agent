from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timedelta
from fastapi import HTTPException

from .config import CFG, logger
from .models import Plan


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
        elif CFG.LLM_PROVIDER == "openai":  # pragma: no cover - network dependent
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

