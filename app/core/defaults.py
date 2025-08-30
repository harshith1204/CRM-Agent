from __future__ import annotations

from datetime import datetime, timedelta, timezone
from .memory import SAVED_REPORTS
from .models import SavedReport, ReportSpec, ReportSheetSpec


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


