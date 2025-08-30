"""
ReAct-style CRM Agent
=====================

A simplified CRM agent using the ReAct (Reasoning and Acting) pattern.
Each action is preceded by explicit reasoning steps, making the decision-making
process transparent and controllable.

ReAct Pattern:
1. Thought: Analyze the user's request and current context
2. Action: Choose and execute a tool based on reasoning
3. Observation: Process the tool's output
4. Repeat until task is complete

Requirements:
- fastapi
- uvicorn
- pandas
- pymongo
- pydantic>=2
- python-dotenv
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import json
import logging
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import re
from enum import Enum

# ------------------------- Setup -------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("react_agent")

# ------------------------- Config -------------------------
@dataclass
class Config:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "crm")
    ALLOWED_COLLECTIONS: List[str] = field(default_factory=lambda: 
        os.getenv("ALLOWED_COLLECTIONS", "leads,tasks,notes,activity").split(","))
    MAX_ITERATIONS: int = 10
    MAX_ROWS: int = 1000

CFG = Config()

# ------------------------- MongoDB Connection -------------------------
try:
    mongo_client = MongoClient(CFG.MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    db = mongo_client[CFG.MONGO_DB]
    MONGO_AVAILABLE = True
    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.warning(f"⚠️ MongoDB not available: {e}")
    mongo_client = None
    db = None
    MONGO_AVAILABLE = False

# ------------------------- Mock Data -------------------------
MOCK_DATA = {
    "leads": [
        {
            "_id": "lead_001",
            "name": "Acme Corp Deal",
            "company": "Acme Corporation",
            "status": "Qualified",
            "amount": 50000,
            "owner": "Alice",
            "created_date": (datetime.now() - timedelta(days=30)).isoformat()
        },
        {
            "_id": "lead_002",
            "name": "TechCo Expansion",
            "company": "TechCo",
            "status": "Proposal",
            "amount": 75000,
            "owner": "Bob",
            "created_date": (datetime.now() - timedelta(days=15)).isoformat()
        }
    ],
    "tasks": [
        {
            "_id": "task_001",
            "title": "Follow up with Acme",
            "lead_id": "lead_001",
            "status": "Open",
            "due_date": (datetime.now() + timedelta(days=2)).isoformat()
        }
    ]
}

# ------------------------- Tool Definitions -------------------------
class ToolType(str, Enum):
    QUERY_DATA = "query_data"
    AGGREGATE_DATA = "aggregate_data"
    FILTER_DATAFRAME = "filter_dataframe"
    GROUP_DATAFRAME = "group_dataframe"
    EXPORT_DATA = "export_data"
    CALCULATE_METRIC = "calculate_metric"

class Tool:
    """Base class for all tools"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> Any:
        raise NotImplementedError

class QueryDataTool(Tool):
    """Query data from MongoDB collections"""
    def __init__(self):
        super().__init__(
            "query_data",
            "Query documents from a MongoDB collection with optional filters"
        )
    
    def execute(self, collection: str, filters: Dict = None, limit: int = 100) -> pd.DataFrame:
        if collection not in CFG.ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection} not allowed")
        
        if not MONGO_AVAILABLE:
            data = MOCK_DATA.get(collection, [])
            df = pd.DataFrame(data)
            if filters:
                for key, value in filters.items():
                    if key in df.columns:
                        df = df[df[key] == value]
            return df.head(limit)
        
        try:
            query = filters or {}
            cursor = db[collection].find(query).limit(limit)
            data = list(cursor)
            return pd.DataFrame(data) if data else pd.DataFrame()
        except PyMongoError as e:
            logger.error(f"MongoDB query error: {e}")
            return pd.DataFrame()

class AggregateDataTool(Tool):
    """Perform aggregation operations on data"""
    def __init__(self):
        super().__init__(
            "aggregate_data",
            "Aggregate data using MongoDB pipelines"
        )
    
    def execute(self, collection: str, pipeline: List[Dict]) -> pd.DataFrame:
        if collection not in CFG.ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection} not allowed")
        
        if not MONGO_AVAILABLE:
            # Simple mock aggregation
            data = MOCK_DATA.get(collection, [])
            return pd.DataFrame(data)
        
        try:
            cursor = db[collection].aggregate(pipeline)
            data = list(cursor)
            return pd.DataFrame(data) if data else pd.DataFrame()
        except PyMongoError as e:
            logger.error(f"MongoDB aggregation error: {e}")
            return pd.DataFrame()

class DataFrameTool(Tool):
    """Perform DataFrame operations"""
    def __init__(self):
        super().__init__(
            "dataframe_ops",
            "Filter, group, and transform DataFrames"
        )
    
    def execute(self, df: pd.DataFrame, operation: str, **params) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        
        if operation == "filter":
            query = params.get("query", "")
            return df.query(query) if query else df
        
        elif operation == "groupby":
            by = params.get("by", [])
            agg = params.get("agg", {})
            if by and agg:
                return df.groupby(by).agg(agg).reset_index()
            return df
        
        elif operation == "sort":
            by = params.get("by", [])
            ascending = params.get("ascending", True)
            return df.sort_values(by=by, ascending=ascending)
        
        return df

class CalculateMetricTool(Tool):
    """Calculate business metrics"""
    def __init__(self):
        super().__init__(
            "calculate_metric",
            "Calculate KPIs and business metrics from data"
        )
    
    def execute(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        if df is None or df.empty:
            return {"error": "No data available"}
        
        if metric == "total_pipeline":
            if "amount" in df.columns:
                return {
                    "metric": "total_pipeline",
                    "value": df["amount"].sum(),
                    "count": len(df)
                }
        
        elif metric == "conversion_rate":
            if "status" in df.columns:
                total = len(df)
                won = len(df[df["status"] == "Won"]) if total > 0 else 0
                rate = (won / total * 100) if total > 0 else 0
                return {
                    "metric": "conversion_rate",
                    "value": f"{rate:.1f}%",
                    "won": won,
                    "total": total
                }
        
        elif metric == "avg_deal_size":
            if "amount" in df.columns:
                return {
                    "metric": "avg_deal_size",
                    "value": df["amount"].mean(),
                    "count": len(df)
                }
        
        return {"error": f"Unknown metric: {metric}"}

# ------------------------- ReAct Agent -------------------------
class ReActStep(BaseModel):
    """Represents a single step in the ReAct process"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[Any] = None

class ReActAgent:
    """
    ReAct Agent that follows the Thought-Action-Observation pattern
    """
    def __init__(self):
        self.tools = {
            "query_data": QueryDataTool(),
            "aggregate_data": AggregateDataTool(),
            "dataframe_ops": DataFrameTool(),
            "calculate_metric": CalculateMetricTool()
        }
        self.context = {}
        self.steps: List[ReActStep] = []
        self.current_df: Optional[pd.DataFrame] = None
    
    def think(self, user_input: str, context: Dict = None) -> str:
        """
        Generate a thought about what to do next based on user input and context
        """
        # Simple rule-based reasoning (replace with LLM in production)
        thought = f"Analyzing request: '{user_input}'"
        
        # Pattern matching for common requests
        patterns = {
            r"(show|get|list|find).*leads": "Need to query leads data",
            r"(total|sum|count).*pipeline": "Need to calculate pipeline metrics",
            r"(group|aggregate).*by\s+(\w+)": "Need to group data by a field",
            r"(filter|where).*status": "Need to filter by status",
            r"conversion.*rate": "Need to calculate conversion rate",
            r"average.*deal": "Need to calculate average deal size",
            r"export|excel|csv": "Need to export data",
            r"top\s+(\d+)": "Need to get top N records"
        }
        
        for pattern, reasoning in patterns.items():
            if re.search(pattern, user_input.lower()):
                thought = f"{thought}. {reasoning}"
                break
        
        return thought
    
    def decide_action(self, thought: str, user_input: str) -> tuple[str, Dict]:
        """
        Decide which action to take based on the thought
        """
        user_lower = user_input.lower()
        
        # Decision tree for actions
        if "query" in thought.lower() or "leads data" in thought.lower():
            # Extract filters if any
            filters = {}
            if "status" in user_lower:
                # Try to extract status value
                for status in ["qualified", "proposal", "won", "lost"]:
                    if status in user_lower:
                        filters["status"] = status.capitalize()
                        break
            
            if "owner" in user_lower:
                # Try to extract owner name
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() == "owner" and i + 1 < len(words):
                        filters["owner"] = words[i + 1].capitalize()
                        break
            
            return "query_data", {
                "collection": "leads",
                "filters": filters,
                "limit": 100
            }
        
        elif "calculate" in thought.lower() or "metrics" in thought.lower():
            if "conversion" in user_lower:
                return "calculate_metric", {"metric": "conversion_rate"}
            elif "average" in user_lower and "deal" in user_lower:
                return "calculate_metric", {"metric": "avg_deal_size"}
            elif "pipeline" in user_lower or "total" in user_lower:
                return "calculate_metric", {"metric": "total_pipeline"}
        
        elif "group" in thought.lower() and self.current_df is not None:
            # Extract groupby field
            match = re.search(r"by\s+(\w+)", user_lower)
            if match:
                field = match.group(1)
                return "dataframe_ops", {
                    "operation": "groupby",
                    "by": [field],
                    "agg": {"amount": "sum", "_id": "count"}
                }
        
        elif "filter" in thought.lower() and self.current_df is not None:
            # Build filter query
            conditions = []
            if "status" in user_lower:
                for status in ["qualified", "proposal", "won", "lost"]:
                    if status in user_lower:
                        conditions.append(f"status == '{status.capitalize()}'")
            
            if conditions:
                return "dataframe_ops", {
                    "operation": "filter",
                    "query": " & ".join(conditions)
                }
        
        # Default: query all leads
        return "query_data", {"collection": "leads", "limit": 100}
    
    def execute_action(self, action: str, action_input: Dict) -> Any:
        """
        Execute the chosen action with the given input
        """
        if action not in self.tools:
            return f"Error: Unknown action {action}"
        
        tool = self.tools[action]
        
        # Special handling for dataframe operations
        if action == "dataframe_ops" and self.current_df is not None:
            return tool.execute(self.current_df, **action_input)
        elif action == "calculate_metric" and self.current_df is not None:
            return tool.execute(self.current_df, **action_input)
        else:
            result = tool.execute(**action_input)
            if isinstance(result, pd.DataFrame):
                self.current_df = result
            return result
    
    def observe(self, result: Any) -> str:
        """
        Process and interpret the action result
        """
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "No data found"
            else:
                return f"Retrieved {len(result)} records with columns: {list(result.columns)}"
        elif isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            else:
                return f"Result: {json.dumps(result, indent=2)}"
        else:
            return str(result)
    
    def should_continue(self, observation: str, user_input: str) -> bool:
        """
        Decide whether to continue with more actions
        """
        # Simple heuristics
        if "error" in observation.lower():
            return False
        
        # Check if we've answered the user's request
        keywords = ["retrieved", "result", "calculated", "found"]
        if any(keyword in observation.lower() for keyword in keywords):
            return False
        
        # Continue if we haven't reached max iterations
        return len(self.steps) < CFG.MAX_ITERATIONS
    
    def run(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """
        Run the ReAct loop for a user input
        """
        self.steps = []
        self.context = context or {}
        self.current_df = None
        
        iteration = 0
        final_result = None
        
        while iteration < CFG.MAX_ITERATIONS:
            # 1. Think
            thought = self.think(user_input, self.context)
            
            # 2. Decide Action
            action, action_input = self.decide_action(thought, user_input)
            
            # 3. Execute Action
            result = self.execute_action(action, action_input)
            
            # 4. Observe
            observation = self.observe(result)
            
            # Record step
            step = ReActStep(
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation
            )
            self.steps.append(step)
            
            # Update context
            self.context["last_observation"] = observation
            final_result = result
            
            # 5. Decide whether to continue
            if not self.should_continue(observation, user_input):
                break
            
            iteration += 1
        
        return self.format_response(final_result)
    
    def format_response(self, result: Any) -> Dict[str, Any]:
        """
        Format the final response for the API
        """
        response = {
            "success": True,
            "steps": [step.model_dump() for step in self.steps],
            "iterations": len(self.steps)
        }
        
        if isinstance(result, pd.DataFrame):
            response["data"] = result.to_dict(orient="records")
            response["shape"] = {"rows": len(result), "columns": len(result.columns)}
            response["columns"] = list(result.columns)
        elif isinstance(result, dict):
            response["data"] = result
        else:
            response["data"] = str(result)
        
        # Add summary
        if self.steps:
            last_step = self.steps[-1]
            response["summary"] = last_step.observation
        
        return response

# ------------------------- API -------------------------
app = FastAPI(title="ReAct CRM Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = ReActAgent()

# ------------------------- API Models -------------------------
class QueryRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    success: bool
    data: Any
    steps: List[Dict[str, Any]]
    iterations: int
    summary: Optional[str] = None
    shape: Optional[Dict[str, int]] = None
    columns: Optional[List[str]] = None

# ------------------------- API Endpoints -------------------------
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a natural language query using the ReAct agent
    """
    try:
        result = agent.run(request.message, request.context)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return QueryResponse(
            success=False,
            data={"error": str(e)},
            steps=[],
            iterations=0,
            summary=f"Error: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ReAct CRM Agent",
        "version": "1.0.0",
        "description": "A ReAct-style agent for CRM data queries",
        "endpoints": {
            "/query": "POST - Process natural language queries",
            "/health": "GET - Health check",
            "/tools": "GET - List available tools",
            "/collections": "GET - List available collections"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mongodb": MONGO_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tools")
async def list_tools():
    """List available tools and their descriptions"""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in agent.tools.values()
        ]
    }

@app.get("/collections")
async def list_collections():
    """List available collections"""
    return {
        "collections": CFG.ALLOWED_COLLECTIONS,
        "database": CFG.MONGO_DB
    }

# ------------------------- Example Usage -------------------------
if __name__ == "__main__":
    import uvicorn
    
    print("""
    ReAct CRM Agent Started
    =======================
    
    Example queries:
    - "Show me all qualified leads"
    - "Calculate the total pipeline value"
    - "What's the conversion rate?"
    - "Group leads by owner"
    - "Find leads with status Proposal"
    - "Calculate average deal size"
    
    API Endpoints:
    - POST /query - Process natural language queries
    - GET /health - Health check
    - GET /tools - List available tools
    - GET /collections - List available collections
    
    The agent follows the ReAct pattern:
    1. Thought: Analyzes the request
    2. Action: Chooses and executes a tool
    3. Observation: Processes the result
    4. Repeats if necessary
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)