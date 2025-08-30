from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from .config import CFG, logger


class ToolContext:
    def __init__(self, mongo_client: MongoClient, db_name: str):
        self.client = mongo_client
        self.db = mongo_client[db_name]


try:
    mongo_client: Optional[MongoClient] = MongoClient(CFG.MONGO_URI, serverSelectionTimeoutMS=2000)
    assert mongo_client is not None
    mongo_client.server_info()
    ctx: Optional[ToolContext] = ToolContext(mongo_client, CFG.MONGO_DB)
    MONGO_AVAILABLE = True
    print("✅ Connected to MongoDB")
except Exception as e:  # pragma: no cover - runtime fallback
    print(f"⚠️ MongoDB not available: {e}")
    print("🔄 Using mock data for demonstration")
    mongo_client = None
    ctx = None
    MONGO_AVAILABLE = False


# Minimal mock dataset used when Mongo is unavailable
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


