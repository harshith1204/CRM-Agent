from __future__ import annotations

from typing import Any, Dict

# Minimal LangGraph-based orchestration that plans using existing planner and executes with existing tools
try:
    from langgraph.graph import StateGraph, START, END  # type: ignore
except Exception:  # pragma: no cover
    # Allow importing even if langgraph isn't installed yet; runtime will fail gracefully
    StateGraph = None  # type: ignore
    START = "START"  # type: ignore
    END = "END"  # type: ignore


def _plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Late import to avoid circular imports during app startup
    import crm_agent_full as core

    schema_catalog = core.build_schema_catalog()
    history = core.MEMORY.get(state["session_id"]) + [{"role": "user", "content": state["message"]}]
    plan = core.client.plan(
        system=(core.SYSTEM_PROMPT + f"\nSchema catalog: {core.json.dumps(schema_catalog)[:2000]}"),
        messages=history,
        tools_schema=core.TOOLS_SCHEMA,
    )
    state.update({
        "plan": plan,
        "schema_catalog": schema_catalog,
    })
    return state


def _act_node(state: Dict[str, Any]) -> Dict[str, Any]:
    import crm_agent_full as core

    result = core.execute_plan(state["session_id"], state["user_id"], state["plan"])
    state.update({
        "result": result,
    })
    return state


def _respond_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Shape response to match existing ChatResponse to keep frontend compatibility
    import crm_agent_full as core

    current_time = core.datetime.now(core.timezone.utc).isoformat()
    res = state.get("result", {})
    # Persist assistant message in memory for session continuity
    core.MEMORY.append(state["session_id"], "assistant", res.get("message", ""))

    return {
        "message": res.get("message", ""),
        "preview_rows": res.get("preview_rows", []),
        "artifacts": res.get("artifacts", {}),
        "embed_urls": res.get("embed_urls", []),
        "plan": state.get("plan").model_dump() if state.get("plan") else {},
        "schema_catalog": state.get("schema_catalog", {}),
        "timestamp": current_time,
        "session_info": core.SESSION_METADATA.get(state["session_id"], {}),
    }


def build_graph():
    if StateGraph is None:
        raise RuntimeError("LangGraph is not installed. Please add 'langgraph' to requirements and install it.")

    graph = StateGraph(dict)
    graph.add_node("plan", _plan_node)
    graph.add_node("act", _act_node)
    graph.add_node("respond", _respond_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "act")
    graph.add_edge("act", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


_GRAPH = None


def run_langgraph_chat(session_id: str, user_id: str, message: str) -> Dict[str, Any]:
    """Run a ReAct-style flow using LangGraph while delegating planning and tools to existing core."""
    import crm_agent_full as core

    # Ensure session metadata and memory are updated similar to core /chat endpoint
    current_time = core.datetime.now(core.timezone.utc).isoformat()
    if session_id not in core.SESSION_METADATA:
        core.SESSION_METADATA[session_id] = {
            "user_id": user_id,
            "created_at": current_time,
            "last_activity": current_time,
            "message_count": 0,
        }
    core.SESSION_METADATA[session_id]["last_activity"] = current_time
    core.SESSION_METADATA[session_id]["message_count"] += 1

    # Save user message
    core.MEMORY.append(session_id, "user", message)

    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()

    initial_state = {
        "session_id": session_id,
        "user_id": user_id,
        "message": message,
    }
    final_state = _GRAPH.invoke(initial_state)
    return final_state

