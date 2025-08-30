#!/usr/bin/env python3
"""
Full-stack CRM Agent Setup Script

This script helps set up both the backend and frontend for the CRM Agent application.
It initializes the database with sample data and provides instructions for running the full stack.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import PyMongoError

def setup_mongodb_with_sample_data():
    """Set up MongoDB with sample CRM data"""
    print("🔧 Setting up MongoDB with sample data...")
    
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["crm"]
        
        # Sample leads data
        leads_data = [
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
                "updated_date": (datetime.now() - timedelta(days=2)).isoformat()
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
                "updated_date": (datetime.now() - timedelta(days=1)).isoformat()
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
                "updated_date": (datetime.now() - timedelta(days=3)).isoformat()
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
                "updated_date": (datetime.now() - timedelta(days=5)).isoformat()
            },
            {
                "_id": "lead_005",
                "name": "BigCorp Partnership",
                "company": "BigCorp Inc",
                "email": "partnerships@bigcorp.com",
                "owner": "Aryan", 
                "status": "Negotiation",
                "amount": 125000,
                "source": "Trade Show",
                "region": "East",
                "created_date": (datetime.now() - timedelta(days=20)).isoformat(),
                "updated_date": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
        
        # Sample tasks
        tasks_data = [
            {
                "_id": "task_001",
                "title": "Follow up with Acme Corp",
                "lead_id": "lead_001", 
                "owner_id": "Priya",
                "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "priority": "High",
                "status": "Open",
                "created_date": datetime.now().isoformat()
            },
            {
                "_id": "task_002",
                "title": "Prepare Globex proposal",
                "lead_id": "lead_002",
                "owner_id": "Aryan", 
                "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                "priority": "Medium",
                "status": "In Progress",
                "created_date": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
        
        # Sample activities
        activity_data = [
            {
                "_id": "activity_001",
                "lead_id": "lead_001",
                "type": "email",
                "when": (datetime.now() - timedelta(days=2)).isoformat(),
                "notes": "Sent proposal document and pricing",
                "created_by": "Priya"
            },
            {
                "_id": "activity_002", 
                "lead_id": "lead_002",
                "type": "meeting",
                "when": (datetime.now() - timedelta(days=1)).isoformat(),
                "notes": "Discovery call completed, identified key requirements",
                "created_by": "Aryan"
            }
        ]
        
        # Sample notes
        notes_data = [
            {
                "_id": "note_001",
                "lead_id": "lead_001",
                "body": "Client interested in annual contract. Need to provide volume discount pricing.",
                "created_date": (datetime.now() - timedelta(days=3)).isoformat(),
                "created_by": "Priya"
            },
            {
                "_id": "note_002",
                "lead_id": "lead_002", 
                "body": "Technical requirements are complex. May need custom development.",
                "created_date": (datetime.now() - timedelta(days=2)).isoformat(),
                "created_by": "Aryan"
            }
        ]
        
        # Insert or update data
        collections_data = {
            "leads": leads_data,
            "tasks": tasks_data, 
            "activity": activity_data,
            "notes": notes_data
        }
        
        for collection_name, data in collections_data.items():
            collection = db[collection_name]
            for item in data:
                collection.replace_one({"_id": item["_id"]}, item, upsert=True)
            print(f"✅ Inserted {len(data)} records into {collection_name}")
            
        print("✅ MongoDB setup completed successfully!")
        return True
        
    except PyMongoError as e:
        print(f"❌ MongoDB error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import fastapi, uvicorn, pandas, pymongo
        print("✅ Python dependencies found")
    except ImportError as e:
        print(f"❌ Missing Python dependencies: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Check Node.js and npm
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("✅ Node.js and npm found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js or npm not found. Please install Node.js.")
        return False
    
    return True

def setup_frontend():
    """Set up the frontend dependencies"""
    print("📦 Setting up frontend dependencies...")
    
    frontend_dir = "/workspace/frontend"
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return False
    
    try:
        # Install npm dependencies
        result = subprocess.run(
            ["npm", "install"], 
            cwd=frontend_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend setup failed: {e.stderr}")
        return False

def create_env_file():
    """Create .env file with default configuration"""
    print("⚙️ Creating environment configuration...")
    
    env_content = """# CRM Agent Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=crm
ALLOWED_COLLECTIONS=leads,tasks,notes,call_logs,activity

# LLM Configuration (set to openai for real LLM)
LLM_PROVIDER=json_stub
# OPENAI_API_KEY=your_openai_key_here
# OPENAI_MODEL=gpt-4o-mini

# Optional: Metabase Integration
# METABASE_SITE_URL=https://your-metabase.com
# METABASE_USERNAME=user@example.com
# METABASE_PASSWORD=password
# METABASE_EMBED_SECRET=your-embed-secret

# Optional: External CRM Integration
# SWAGGER_SPEC_URL=https://your-crm.com/swagger/v1/swagger.json
# SWAGGER_BASE_URL=https://your-crm.com
# SWAGGER_AUTH_HEADER=Authorization
# SWAGGER_AUTH_VALUE=Bearer YOUR_TOKEN
"""
    
    env_path = "/workspace/.env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(env_content)
        print(f"✅ Created {env_path}")
    else:
        print(f"ℹ️ Environment file already exists: {env_path}")
    
    return True

def print_startup_instructions():
    """Print instructions for starting the application"""
    print("\n🚀 Setup Complete! Here's how to start the application:\n")
    
    print("1. Start MongoDB (if not already running):")
    print("   docker run -d -p 27017:27017 --name mongodb mongo:latest")
    print("   # OR if using local MongoDB:")
    print("   # mongod --dbpath /your/db/path\n")
    
    print("2. Start the Backend API:")
    print("   cd /workspace")
    print("   python crm_agent_full.py")
    print("   # OR")
    print("   # uvicorn crm_agent_full:app --reload --host 0.0.0.0 --port 8000\n")
    
    print("3. Start the Frontend (in a new terminal):")
    print("   cd /workspace/frontend") 
    print("   npm run dev\n")
    
    print("4. Access the application:")
    print("   Frontend: http://localhost:5173")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs\n")
    
    print("🎯 Features available:")
    print("   • Dashboard with real-time KPIs")
    print("   • Conversational AI agent with chat interface")
    print("   • Data explorer with filtering and export")
    print("   • Report builder with saved reports")
    print("   • Artifact management and downloads")
    print("   • Metabase integration (if configured)")
    print("   • CRM write operations (if configured)\n")

def main():
    """Main setup function"""
    print("🏗️ CRM Agent Full-Stack Setup\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        sys.exit(1)
    
    # Setup MongoDB with sample data
    if not setup_mongodb_with_sample_data():
        print("⚠️ MongoDB setup failed, but you can continue with manual setup")
    
    # Print startup instructions
    print_startup_instructions()
    
    print("✅ Setup completed successfully!")

if __name__ == "__main__":
    main()