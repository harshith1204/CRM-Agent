#!/usr/bin/env python3
"""
Test Examples for CRM Agent

This script demonstrates various ways to interact with the CRM Agent API.
Make sure the server is running before executing these tests.

Usage:
    python test_examples.py
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_info():
    """Test the info endpoint."""
    print("ℹ️  Testing info endpoint...")
    response = requests.get(f"{BASE_URL}/info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_chat_analytics():
    """Test analytics query via chat."""
    print("📊 Testing analytics query...")
    payload = {
        "session_id": "analytics_test",
        "user_id": "alice",
        "message": "Show me all leads grouped by owner with total amounts, and export to Excel"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Preview rows: {len(data.get('preview_rows', []))}")
        print(f"Artifacts: {list(data.get('artifacts', {}).keys())}")
        print(f"Plan intent: {data['plan']['intent']}")
        
        # Download Excel if available
        if 'excel' in data.get('artifacts', {}):
            artifact_url = data['artifacts']['excel']['download_url']
            print(f"📥 Excel download available at: {BASE_URL}{artifact_url}")
    else:
        print(f"Error: {response.text}")
    print()

def test_metabase_embed():
    """Test Metabase embed URL generation."""
    print("📈 Testing Metabase embed...")
    payload = {
        "session_id": "metabase_test",
        "user_id": "manager",
        "message": "Show me the sales dashboard from Metabase as an embed"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Embed URLs: {data.get('embed_urls', [])}")
    else:
        print(f"Error: {response.text}")
    print()

def test_report_builder():
    """Test the report builder functionality."""
    print("📑 Testing report builder...")
    payload = {
        "session_id": "report_test",
        "user_id": "admin",
        "message": "Build a comprehensive pipeline report"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Artifacts: {list(data.get('artifacts', {}).keys())}")
        
        # Download report if available
        if 'report' in data.get('artifacts', {}):
            artifact_url = data['artifacts']['report']['download_url']
            print(f"📥 Report download available at: {BASE_URL}{artifact_url}")
    else:
        print(f"Error: {response.text}")
    print()

def test_conversational_context():
    """Test conversational context preservation."""
    print("💬 Testing conversational context...")
    session_id = f"context_test_{int(time.time())}"
    
    # First message
    payload1 = {
        "session_id": session_id,
        "user_id": "alice",
        "message": "Show me leads owned by alice"
    }
    
    response1 = requests.post(f"{BASE_URL}/chat", json=payload1)
    print(f"First message status: {response1.status_code}")
    if response1.status_code == 200:
        print(f"First response: {response1.json()['message']}")
    
    # Second message in same session
    payload2 = {
        "session_id": session_id,
        "user_id": "alice", 
        "message": "Now export those results to Excel"
    }
    
    response2 = requests.post(f"{BASE_URL}/chat", json=payload2)
    print(f"Second message status: {response2.status_code}")
    if response2.status_code == 200:
        data = response2.json()
        print(f"Second response: {data['message']}")
        print(f"Context preserved: {'excel' in data.get('artifacts', {})}")
    print()

def test_plan_only():
    """Test plan generation without execution."""
    print("🎯 Testing plan generation...")
    payload = {
        "session_id": "plan_test",
        "user_id": "alice",
        "message": "Create a chart showing leads by status and export to Excel"
    }
    
    response = requests.post(f"{BASE_URL}/plan", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        plan = data['plan']
        print(f"Intent: {plan['intent']}")
        print(f"Tool calls: {len(plan['tool_calls'])}")
        for i, tool_call in enumerate(plan['tool_calls'], 1):
            print(f"  {i}. {tool_call['tool']}")
    else:
        print(f"Error: {response.text}")
    print()

def run_all_tests():
    """Run all test examples."""
    print("🧪 Running CRM Agent Test Examples")
    print("=" * 50)
    
    try:
        test_health()
        test_info()
        test_analytics()
        test_metabase_embed()
        test_report_builder()
        test_conversational_context()
        test_plan_only()
        
        print("✅ All tests completed!")
        print("\n💡 Next steps:")
        print("   • Check the interactive docs at http://localhost:8000/docs")
        print("   • Download any generated artifacts from the URLs above")
        print("   • Try your own custom queries via the /chat endpoint")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the CRM Agent server is running:")
        print("   uvicorn crm_agent_full:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    run_all_tests()
