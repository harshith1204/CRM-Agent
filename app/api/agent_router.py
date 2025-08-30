from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.langgraph_agent import run_langgraph_chat


router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


@router.post("/chat")
def agent_chat(req: AgentChatRequest):
    try:
        return run_langgraph_chat(req.session_id, req.user_id, req.message)
    except RuntimeError as e:
        # Surface dependency/setup issues clearly
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

