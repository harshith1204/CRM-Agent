# CRM Agent API Examples

This document provides comprehensive examples of how to use the CRM Agent API for various use cases.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Analytics & Reporting](#analytics--reporting)
- [Metabase Integration](#metabase-integration)
- [CRM Operations](#crm-operations)
- [Conversational Context](#conversational-context)
- [Advanced Examples](#advanced-examples)

## Basic Setup

### Start the Server
```bash
uvicorn crm_agent_full:app --reload
```

### Test Connection
```bash
curl http://localhost:8000/health
```

## Analytics & Reporting

### 1. Basic Lead Analytics

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "analytics_1",
    "user_id": "analyst",
    "message": "Show me all leads grouped by status with counts"
  }'
```

**Expected Response:**
- Preview of grouped data
- Downloadable Excel report
- Plan showing mongo.read + df.op tools

### 2. Sales Pipeline Report

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "pipeline_1", 
    "user_id": "manager",
    "message": "Create a sales pipeline report showing leads by owner with total amounts, include a bar chart"
  }'
```

**Expected Response:**
- Excel export with pipeline data
- Bar chart PNG artifact
- Preview of aggregated data

### 3. Time-based Analysis

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "time_analysis",
    "user_id": "analyst", 
    "message": "Show me leads created in the last 30 days, group by week and show trend chart"
  }'
```

### 4. Advanced Filtering

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "filtering_1",
    "user_id": "alice",
    "message": "Find high-value leads (>$70k) that haven been contacted in the last 7 days"
  }'
```

## Metabase Integration

### 1. Dashboard Embed

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "dashboard_1",
    "user_id": "manager",
    "message": "Show me the sales performance dashboard from Metabase as an embed"
  }'
```

**Expected Response:**
- Signed embed URL for dashboard
- JWT token with expiration
- Theme and display options

### 2. Question Embed with Parameters

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "question_1",
    "user_id": "analyst",
    "message": "Embed the monthly revenue question from Metabase for this quarter"
  }'
```

### 3. Query Metabase Card Data

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "card_query_1",
    "user_id": "analyst",
    "message": "Get data from Metabase card 123 and export to Excel"
  }'
```

## CRM Operations

### 1. Create Follow-up Tasks

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "tasks_1",
    "user_id": "alice",
    "message": "Create follow-up tasks for all leads in Contacted status, due next Friday"
  }'
```

### 2. Log Customer Calls

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "calls_1",
    "user_id": "bob",
    "message": "Log a 30-minute outbound call with lead John Doe discussing pricing"
  }'
```

### 3. Add Notes to Leads

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "notes_1",
    "user_id": "alice",
    "message": "Add a note to Mike Johnson lead: Customer approved budget, moving to proposal stage"
  }'
```

### 4. Update Lead Status

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "update_1",
    "user_id": "manager",
    "message": "Update Jane Smith lead status to Qualified and set amount to $85000"
  }'
```

## Conversational Context

### Multi-turn Conversation

**Turn 1:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "conversation_1",
    "user_id": "alice",
    "message": "Show me my leads"
  }'
```

**Turn 2:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "conversation_1",
    "user_id": "alice",
    "message": "Filter those to only show high priority ones"
  }'
```

**Turn 3:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "conversation_1", 
    "user_id": "alice",
    "message": "Export this filtered list to Excel"
  }'
```

## Advanced Examples

### 1. Multi-Sheet Report Builder

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "advanced_report_1",
    "user_id": "admin",
    "message": "Build a comprehensive weekly report with: 1) Pipeline summary from Metabase card 101, 2) Recent activities from MongoDB, 3) Overdue tasks analysis"
  }'
```

### 2. Complex Analytics Workflow

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "complex_analytics_1",
    "user_id": "analyst",
    "message": "Analyze lead conversion rates by source, create a funnel chart, and identify the top 3 performing sources"
  }'
```

### 3. Automated Task Creation

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "automation_1",
    "user_id": "manager",
    "message": "Find all leads that haven been contacted in 14 days and create follow-up tasks for each, due in 2 days"
  }'
```

### 4. Performance Dashboard Creation

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "performance_1",
    "user_id": "executive",
    "message": "Create a performance dashboard showing: sales by rep, conversion rates, and top opportunities. Include both charts and Metabase embeds"
  }'
```

## Response Handling Examples

### JavaScript/Frontend Integration

```javascript
async function queryCRM(sessionId, userId, message) {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            user_id: userId,
            message: message
        })
    });
    
    const data = await response.json();
    
    // Handle response
    console.log('Message:', data.message);
    
    // Display preview data
    if (data.preview_rows.length > 0) {
        console.table(data.preview_rows);
    }
    
    // Handle artifacts (downloads)
    Object.entries(data.artifacts).forEach(([type, artifact]) => {
        console.log(`${type} available at: ${artifact.download_url}`);
    });
    
    // Handle Metabase embeds
    data.embed_urls.forEach(url => {
        console.log('Embed URL:', url);
        // You can iframe these URLs
    });
    
    return data;
}

// Example usage
queryCRM('demo_session', 'user123', 'Show me leads by status with charts');
```

### Python Client Example

```python
import requests
import pandas as pd
from io import BytesIO

class CRMAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def chat(self, session_id: str, user_id: str, message: str):
        response = requests.post(f"{self.base_url}/chat", json={
            "session_id": session_id,
            "user_id": user_id,
            "message": message
        })
        response.raise_for_status()
        return response.json()
    
    def download_artifact(self, artifact_url: str) -> bytes:
        response = requests.get(f"{self.base_url}{artifact_url}")
        response.raise_for_status()
        return response.content
    
    def get_excel_dataframe(self, artifact_url: str) -> pd.DataFrame:
        excel_data = self.download_artifact(artifact_url)
        return pd.read_excel(BytesIO(excel_data))

# Example usage
client = CRMAgentClient()
result = client.chat("demo", "alice", "Show me leads by owner")

if 'excel' in result['artifacts']:
    df = client.get_excel_dataframe(result['artifacts']['excel']['download_url'])
    print(df.head())
```

## Error Handling Examples

### Common Error Responses

#### 1. Invalid Collection Access
```json
{
  "detail": "User not allowed to access collection sensitive_data",
  "status_code": 403
}
```

#### 2. MongoDB Connection Error
```json
{
  "detail": "MongoDB connection failed: connection timeout",
  "status_code": 500
}
```

#### 3. Metabase Configuration Error
```json
{
  "detail": "Metabase site not configured",
  "status_code": 503
}
```

#### 4. Invalid Tool Parameters
```json
{
  "detail": "Validation error for mongo.read: collection is required",
  "status_code": 400
}
```

### Robust Error Handling in Client Code

```python
def safe_crm_query(session_id, user_id, message):
    try:
        response = requests.post("http://localhost:8000/chat", json={
            "session_id": session_id,
            "user_id": user_id,
            "message": message
        }, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"error": "Access denied - check user permissions"}
        elif response.status_code == 503:
            return {"error": "Service unavailable - check configuration"}
        else:
            return {"error": f"API error: {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to CRM Agent - is the server running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - try a simpler query"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

## Testing Your Setup

### 1. Verify MongoDB Connection
```bash
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
print('✅ MongoDB connected:', client.admin.command('ismaster')['ok'])
"
```

### 2. Test Basic Chat
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","user_id":"alice","message":"hello"}' | jq .
```

### 3. Check Available Collections
```bash
curl http://localhost:8000/info | jq .collections
```

### 4. Generate Sample Data
```bash
python setup_mongodb.py
```

### 5. Run Full Test Suite
```bash
python test_examples.py
```

## Production Considerations

### 1. Authentication Middleware

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement your token verification logic
    if not verify_jwt_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return extract_user_from_token(token.credentials)

# Add to endpoints:
@app.post("/chat")
def chat(req: ChatRequest, user=Depends(verify_token)):
    # Use verified user instead of req.user_id
    pass
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, req: ChatRequest):
    pass
```

### 3. Persistent Conversation Storage

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class PersistentChatMemory:
    def get(self, session_id: str) -> List[Dict[str, str]]:
        data = redis_client.get(f"session:{session_id}")
        return json.loads(data) if data else []
    
    def append(self, session_id: str, role: str, content: str):
        history = self.get(session_id)
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        redis_client.setex(f"session:{session_id}", 3600, json.dumps(history))
```

### 4. Monitoring and Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('crm_agent_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_DURATION = Histogram('crm_agent_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(endpoint=request.url.path, method=request.method).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "No tools executed" Message
- **Cause**: LLM_PROVIDER is set to `json_stub`
- **Solution**: Set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY`

#### 2. MongoDB Connection Timeout
- **Cause**: MongoDB not running or incorrect URI
- **Solution**: 
  ```bash
  # Start MongoDB
  sudo systemctl start mongod
  # Or with Docker
  docker run -d -p 27017:27017 mongo:7.0
  ```

#### 3. Metabase Embed URLs Not Working
- **Cause**: Missing embed secret or incorrect configuration
- **Solution**: 
  - Verify `METABASE_EMBED_SECRET` in Metabase admin settings
  - Check `METABASE_SITE_URL` is accessible
  - Ensure embedding is enabled for the resource

#### 4. Swagger Integration Failing
- **Cause**: API specification not accessible or incorrect auth
- **Solution**:
  - Test `SWAGGER_SPEC_URL` manually in browser
  - Verify `SWAGGER_AUTH_VALUE` token is valid
  - Check API base URL and endpoints

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("crm_agent").setLevel(logging.DEBUG)
```

### Health Checks

```bash
# MongoDB
curl http://localhost:8000/info | jq '.collections'

# Metabase
curl http://localhost:8000/info | jq '.metabase_configured'

# Swagger
curl http://localhost:8000/info | jq '.swagger_configured'
```

## Performance Optimization

### 1. MongoDB Indexing

```javascript
// Run in MongoDB shell
use crm;

// Lead indexes
db.leads.createIndex({"owner": 1, "status": 1});
db.leads.createIndex({"created_at": -1});
db.leads.createIndex({"amount": -1});

// Task indexes  
db.tasks.createIndex({"owner_id": 1, "due_date": 1});
db.tasks.createIndex({"lead_id": 1});

// Activity indexes
db.activity.createIndex({"lead_id": 1, "when": -1});
```

### 2. Caching Strategy

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_schema_catalog():
    return build_schema_catalog()

# Cache Metabase session tokens
class CachedMetabaseClient(MetabaseClient):
    def __init__(self):
        super().__init__()
        self._token_expires = 0
    
    def ensure_session(self):
        if time.time() > self._token_expires:
            self.login(CFG.METABASE_USERNAME, CFG.METABASE_PASSWORD)
            self._token_expires = time.time() + 3600  # 1 hour
```

### 3. Async Operations

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def async_mongo_read(spec: MongoReadSpec) -> pd.DataFrame:
    client = AsyncIOMotorClient(CFG.MONGO_URI)
    db = client[CFG.MONGO_DB]
    cursor = db[spec.collection].aggregate(spec.pipeline)
    rows = await cursor.to_list(length=spec.limit)
    return pd.json_normalize(rows)
```

This completes the API examples documentation with practical usage patterns, error handling, and production considerations.
