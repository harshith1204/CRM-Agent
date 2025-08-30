from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_router import router as agent_router
from app.api.core_router import router as core_router


app = FastAPI(title="CRM Agent (Modular)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "CRM Agent API (Modular)", "version": "1.0", "docs": "/docs"}


app.include_router(core_router)
app.include_router(agent_router)

