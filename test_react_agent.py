"""
Test script for the ReAct CRM Agent
====================================

This script demonstrates how to use the ReAct agent directly
without running the FastAPI server.
"""

import json
from react_crm_agent import ReActAgent

def test_react_agent():
    """Test the ReAct agent with various queries"""
    
    # Create agent instance
    agent = ReActAgent()
    
    # Test queries
    test_queries = [
        "Show me all qualified leads",
        "Calculate the total pipeline value",
        "What's the conversion rate?",
        "Find leads owned by Alice",
        "Group leads by status",
        "Calculate average deal size"
    ]
    
    print("=" * 60)
    print("ReAct CRM Agent Test")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)
        
        # Run the agent
        result = agent.run(query)
        
        # Display the reasoning steps
        for i, step in enumerate(result["steps"], 1):
            print(f"\nStep {i}:")
            print(f"  💭 Thought: {step['thought']}")
            if step['action']:
                print(f"  🎯 Action: {step['action']}")
                print(f"  📥 Input: {json.dumps(step['action_input'], indent=4)}")
            if step['observation']:
                print(f"  👁️ Observation: {step['observation']}")
        
        # Display final result
        print(f"\n✅ Summary: {result.get('summary', 'No summary')}")
        
        if "shape" in result and result["shape"]:
            print(f"📊 Data Shape: {result['shape']['rows']} rows × {result['shape']['columns']} columns")
        
        if isinstance(result.get("data"), list) and len(result["data"]) > 0:
            print(f"📋 Sample Data (first 3 records):")
            for record in result["data"][:3]:
                print(f"   {json.dumps(record, indent=4)}")
        elif isinstance(result.get("data"), dict):
            print(f"📈 Result:")
            print(f"   {json.dumps(result['data'], indent=4)}")
        
        print("=" * 60)

if __name__ == "__main__":
    test_react_agent()