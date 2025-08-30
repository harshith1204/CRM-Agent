#!/usr/bin/env python3
"""
MongoDB Setup Script for CRM Agent

This script creates sample data for testing the CRM Agent application.
Run this script after setting up MongoDB to populate the database with example data.

Usage:
    python setup_mongodb.py
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json
from typing import List, Dict, Any

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "crm")

def connect_to_mongodb() -> MongoClient:
    """Connect to MongoDB and test the connection."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ismaster')
        print(f"✅ Connected to MongoDB at {MONGO_URI}")
        return client
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

def create_sample_leads(db) -> List[str]:
    """Create sample lead records."""
    leads_data = [
        {
            "name": "John Doe",
            "email": "john.doe@techcorp.com",
            "phone": "+1-555-0101",
            "company": "TechCorp Inc",
            "status": "Qualified",
            "owner": "alice",
            "amount": 50000,
            "source": "Website",
            "industry": "Technology",
            "created_at": datetime.now() - timedelta(days=15),
            "last_contacted": datetime.now() - timedelta(days=3),
            "notes_count": 2,
            "activities_count": 5
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@retailplus.com", 
            "phone": "+1-555-0102",
            "company": "RetailPlus",
            "status": "Contacted",
            "owner": "bob",
            "amount": 75000,
            "source": "Referral",
            "industry": "Retail",
            "created_at": datetime.now() - timedelta(days=8),
            "last_contacted": datetime.now() - timedelta(days=1),
            "notes_count": 1,
            "activities_count": 3
        },
        {
            "name": "Mike Johnson",
            "email": "mike.johnson@healthsys.org",
            "phone": "+1-555-0103", 
            "company": "HealthSystems",
            "status": "Proposal",
            "owner": "alice",
            "amount": 120000,
            "source": "Cold Call",
            "industry": "Healthcare",
            "created_at": datetime.now() - timedelta(days=25),
            "last_contacted": datetime.now() - timedelta(days=2),
            "notes_count": 4,
            "activities_count": 8
        },
        {
            "name": "Sarah Wilson",
            "email": "sarah.wilson@edutech.edu",
            "phone": "+1-555-0104",
            "company": "EduTech Solutions",
            "status": "New",
            "owner": "charlie",
            "amount": 35000,
            "source": "Trade Show",
            "industry": "Education",
            "created_at": datetime.now() - timedelta(days=2),
            "last_contacted": None,
            "notes_count": 0,
            "activities_count": 1
        },
        {
            "name": "David Brown",
            "email": "david.brown@financegroup.com",
            "phone": "+1-555-0105",
            "company": "Finance Group LLC",
            "status": "Closed Won",
            "owner": "bob",
            "amount": 95000,
            "source": "LinkedIn",
            "industry": "Finance",
            "created_at": datetime.now() - timedelta(days=45),
            "last_contacted": datetime.now() - timedelta(days=7),
            "notes_count": 6,
            "activities_count": 12
        },
        {
            "name": "Lisa Garcia",
            "email": "lisa.garcia@manufacturing.com",
            "phone": "+1-555-0106",
            "company": "Manufacturing Co",
            "status": "Closed Lost",
            "owner": "alice",
            "amount": 80000,
            "source": "Website",
            "industry": "Manufacturing",
            "created_at": datetime.now() - timedelta(days=60),
            "last_contacted": datetime.now() - timedelta(days=14),
            "notes_count": 3,
            "activities_count": 6
        }
    ]
    
    result = db.leads.insert_many(leads_data)
    lead_ids = [str(id) for id in result.inserted_ids]
    print(f"✅ Created {len(lead_ids)} sample leads")
    return lead_ids

def create_sample_tasks(db, lead_ids: List[str]):
    """Create sample task records."""
    tasks_data = [
        {
            "title": "Follow up call with John Doe",
            "description": "Discuss pricing options and timeline",
            "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "lead_id": lead_ids[0],
            "owner_id": "alice",
            "priority": "high",
            "status": "open",
            "completed": False,
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "title": "Send proposal to Jane Smith",
            "description": "Custom proposal for RetailPlus integration",
            "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "lead_id": lead_ids[1],
            "owner_id": "bob",
            "priority": "medium",
            "status": "in_progress",
            "completed": False,
            "created_at": datetime.now() - timedelta(days=3)
        },
        {
            "title": "Schedule demo for Mike Johnson",
            "description": "Product demonstration for HealthSystems team",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "lead_id": lead_ids[2],
            "owner_id": "alice",
            "priority": "high",
            "status": "open",
            "completed": False,
            "created_at": datetime.now() - timedelta(hours=6)
        },
        {
            "title": "Research EduTech requirements",
            "description": "Understand their specific needs and budget",
            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "lead_id": lead_ids[3],
            "owner_id": "charlie",
            "priority": "low",
            "status": "open",
            "completed": False,
            "created_at": datetime.now() - timedelta(hours=2)
        },
        {
            "title": "Contract finalization with Finance Group",
            "description": "Review and finalize legal terms",
            "due_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "lead_id": lead_ids[4],
            "owner_id": "bob",
            "priority": "high",
            "status": "completed",
            "completed": True,
            "completed_at": datetime.now() - timedelta(days=3),
            "created_at": datetime.now() - timedelta(days=10)
        }
    ]
    
    result = db.tasks.insert_many(tasks_data)
    print(f"✅ Created {len(result.inserted_ids)} sample tasks")

def create_sample_notes(db, lead_ids: List[str]):
    """Create sample note records."""
    notes_data = [
        {
            "lead_id": lead_ids[0],
            "body": "Customer is very interested in our enterprise solution. Budget approved for Q1 implementation.",
            "author": "alice",
            "created_at": datetime.now() - timedelta(days=2),
            "type": "meeting_note"
        },
        {
            "lead_id": lead_ids[0],
            "body": "Sent technical specifications document. Waiting for their technical team review.",
            "author": "alice",
            "created_at": datetime.now() - timedelta(days=1),
            "type": "follow_up"
        },
        {
            "lead_id": lead_ids[1],
            "body": "Initial call went well. They need integration with their existing POS system.",
            "author": "bob",
            "created_at": datetime.now() - timedelta(days=5),
            "type": "call_note"
        },
        {
            "lead_id": lead_ids[2],
            "body": "Healthcare compliance is their main concern. Need to address HIPAA requirements.",
            "author": "alice",
            "created_at": datetime.now() - timedelta(days=7),
            "type": "requirement"
        },
        {
            "lead_id": lead_ids[2],
            "body": "Provided HIPAA compliance documentation. They're reviewing with legal team.",
            "author": "alice",
            "created_at": datetime.now() - timedelta(days=4),
            "type": "follow_up"
        },
        {
            "lead_id": lead_ids[4],
            "body": "Contract signed! Implementation starts next month.",
            "author": "bob",
            "created_at": datetime.now() - timedelta(days=5),
            "type": "success"
        }
    ]
    
    result = db.notes.insert_many(notes_data)
    print(f"✅ Created {len(result.inserted_ids)} sample notes")

def create_sample_call_logs(db, lead_ids: List[str]):
    """Create sample call log records."""
    call_logs_data = [
        {
            "lead_id": lead_ids[0],
            "direction": "outbound",
            "duration_seconds": 1800,  # 30 minutes
            "summary": "Discussed pricing and implementation timeline. Customer ready to move forward.",
            "outcome": "positive",
            "caller": "alice",
            "created_at": datetime.now() - timedelta(days=3)
        },
        {
            "lead_id": lead_ids[1],
            "direction": "inbound", 
            "duration_seconds": 900,  # 15 minutes
            "summary": "Customer called with questions about integration capabilities.",
            "outcome": "neutral",
            "caller": "bob",
            "created_at": datetime.now() - timedelta(days=1)
        },
        {
            "lead_id": lead_ids[2],
            "direction": "outbound",
            "duration_seconds": 2400,  # 40 minutes
            "summary": "Deep dive into security and compliance features.",
            "outcome": "positive",
            "caller": "alice",
            "created_at": datetime.now() - timedelta(days=6)
        },
        {
            "lead_id": lead_ids[4],
            "direction": "outbound",
            "duration_seconds": 600,  # 10 minutes
            "summary": "Contract terms discussion and final approval.",
            "outcome": "closed_won",
            "caller": "bob",
            "created_at": datetime.now() - timedelta(days=8)
        }
    ]
    
    result = db.call_logs.insert_many(call_logs_data)
    print(f"✅ Created {len(result.inserted_ids)} sample call logs")

def create_sample_activities(db, lead_ids: List[str]):
    """Create sample activity records."""
    activities_data = [
        {
            "lead_id": lead_ids[0],
            "type": "email",
            "subject": "Technical Specifications Document",
            "description": "Sent detailed technical specs and architecture diagram",
            "when": datetime.now() - timedelta(days=1),
            "owner": "alice",
            "status": "completed"
        },
        {
            "lead_id": lead_ids[0],
            "type": "meeting",
            "subject": "Requirements Gathering Session",
            "description": "60-minute session to understand their specific needs",
            "when": datetime.now() - timedelta(days=4),
            "owner": "alice",
            "status": "completed"
        },
        {
            "lead_id": lead_ids[1],
            "type": "demo",
            "subject": "Product Demonstration",
            "description": "Live demo of POS integration features",
            "when": datetime.now() + timedelta(days=3),
            "owner": "bob",
            "status": "scheduled"
        },
        {
            "lead_id": lead_ids[2],
            "type": "followup",
            "subject": "HIPAA Compliance Follow-up",
            "description": "Check on legal team review of compliance docs",
            "when": datetime.now() + timedelta(days=1),
            "owner": "alice",
            "status": "planned"
        },
        {
            "lead_id": lead_ids[3],
            "type": "email",
            "subject": "Welcome and Introduction",
            "description": "Initial outreach email with company overview",
            "when": datetime.now() - timedelta(hours=3),
            "owner": "charlie",
            "status": "completed"
        },
        {
            "lead_id": lead_ids[4],
            "type": "meeting",
            "subject": "Contract Signing",
            "description": "Final contract review and signature",
            "when": datetime.now() - timedelta(days=5),
            "owner": "bob",
            "status": "completed"
        }
    ]
    
    result = db.activity.insert_many(activities_data)
    print(f"✅ Created {len(result.inserted_ids)} sample activities")

def create_indexes(db):
    """Create useful indexes for better query performance."""
    # Leads indexes
    db.leads.create_index("owner")
    db.leads.create_index("status")
    db.leads.create_index("created_at")
    db.leads.create_index([("owner", 1), ("status", 1)])
    
    # Tasks indexes
    db.tasks.create_index("owner_id")
    db.tasks.create_index("due_date")
    db.tasks.create_index("lead_id")
    db.tasks.create_index("status")
    
    # Notes indexes
    db.notes.create_index("lead_id")
    db.notes.create_index("author")
    db.notes.create_index("created_at")
    
    # Call logs indexes
    db.call_logs.create_index("lead_id")
    db.call_logs.create_index("direction")
    db.call_logs.create_index("created_at")
    
    # Activities indexes
    db.activity.create_index("lead_id")
    db.activity.create_index("type")
    db.activity.create_index("owner")
    db.activity.create_index("when")
    
    print("✅ Created database indexes")

def print_summary(db):
    """Print a summary of created data."""
    print("\n📊 Database Summary:")
    print(f"  • Leads: {db.leads.count_documents({})}")
    print(f"  • Tasks: {db.tasks.count_documents({})}")
    print(f"  • Notes: {db.notes.count_documents({})}")
    print(f"  • Call Logs: {db.call_logs.count_documents({})}")
    print(f"  • Activities: {db.activity.count_documents({})}")
    
    print("\n📈 Lead Status Distribution:")
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    for doc in db.leads.aggregate(pipeline):
        print(f"  • {doc['_id']}: {doc['count']}")
    
    print("\n👥 Leads by Owner:")
    pipeline = [
        {"$group": {"_id": "$owner", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}},
        {"$sort": {"count": -1}}
    ]
    for doc in db.leads.aggregate(pipeline):
        print(f"  • {doc['_id']}: {doc['count']} leads, ${doc['total_amount']:,} total value")

def main():
    """Main setup function."""
    print("🚀 Setting up MongoDB for CRM Agent...")
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[MONGO_DB]
    
    # Check if data already exists
    if db.leads.count_documents({}) > 0:
        response = input("⚠️  Data already exists. Clear and recreate? (y/N): ")
        if response.lower() == 'y':
            print("🗑️  Clearing existing data...")
            db.leads.delete_many({})
            db.tasks.delete_many({})
            db.notes.delete_many({})
            db.call_logs.delete_many({})
            db.activity.delete_many({})
        else:
            print("✋ Setup cancelled.")
            return
    
    # Create sample data
    print("\n📝 Creating sample data...")
    lead_ids = create_sample_leads(db)
    create_sample_tasks(db, lead_ids)
    create_sample_notes(db, lead_ids)
    create_sample_call_logs(db, lead_ids)
    create_sample_activities(db, lead_ids)
    
    # Create indexes
    print("\n🔍 Creating database indexes...")
    create_indexes(db)
    
    # Print summary
    print_summary(db)
    
    print("\n✅ MongoDB setup complete!")
    print(f"\n🔗 You can now test the CRM Agent with:")
    print("   uvicorn crm_agent_full:app --reload")
    print("\n📖 Or explore the data with MongoDB Compass at:")
    print(f"   {MONGO_URI}")

if __name__ == "__main__":
    main()