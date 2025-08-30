from __future__ import annotations

from typing import Any, Dict, List, Optional
import io
import pandas as pd
import matplotlib.pyplot as plt
from fastapi import HTTPException

from .db import ctx, MONGO_AVAILABLE, MOCK_DATA
from .rbac import rbac_policy
from .models import MongoReadSpec, DataframeOpSpec, PlotSpec, ExcelSpec, MetabaseQuerySpec, MetabaseEmbedSpec
from .metabase_client import metabase


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
    except Exception as e:
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


# Metabase adapters
def metabase_query_df(spec: MetabaseQuerySpec) -> pd.DataFrame:
    return metabase.query_card_dataframe(spec.card_id, spec.params)


def metabase_embed_url(spec: MetabaseEmbedSpec) -> str:
    return metabase.signed_embed_url(spec.resource_type, spec.resource_id, spec.params, theme=spec.theme)


