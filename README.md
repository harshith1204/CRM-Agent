# CRM Agent

A conversational Customer Relationship Management (CRM) agent with analytics, Metabase integration, and MongoDB backend.

## Features

- **Conversational Interface**: Chat-based interaction with persistent session state
- **MongoDB Integration**: Read/write operations on leads, tasks, notes, call logs, and activities
- **Analytics & Reporting**: DataFrame operations, Excel exports, and chart generation
- **Metabase Integration**: 
  - Signed embed URLs for dashboards and questions
  - Query cards via API and export results
- **Multi-sheet Report Builder**: Combine MongoDB and Metabase data
- **CRM Actions**: Create tasks, notes, call logs, activities, and update leads via Swagger/OpenAPI
- **RBAC**: Role-based access control with field-level restrictions
- **Artifact Management**: Downloadable XLSX/PNG files with secure URLs

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration values
   ```

3. **Start the Server**
   ```bash
   uvicorn crm_agent_full:app --reload
   ```

4. **Test the API**
   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"session_id":"demo","user_id":"alice","message":"Build a pipeline by owner report and share a chart"}'
   ```

## Configuration

### Required Environment Variables

#### MongoDB
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `MONGO_DB`: Database name (default: `crm`)
- `ALLOWED_COLLECTIONS`: Comma-separated list of allowed collections

#### LLM Provider
- `LLM_PROVIDER`: Either `json_stub` (for demo) or `openai`
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `OPENAI_MODEL`: Model to use (default: `gpt-4o-mini`)

### Optional Integrations

#### Swagger/OpenAPI Backend
- `SWAGGER_SPEC_URL`: URL to your CRM's OpenAPI specification
- `SWAGGER_BASE_URL`: Base URL for your CRM API
- `SWAGGER_AUTH_HEADER`: Authorization header name
- `SWAGGER_AUTH_VALUE`: Authorization header value

#### Metabase
- `METABASE_SITE_URL`: Your Metabase instance URL
- `METABASE_USERNAME`: Metabase username (optional if using session token)
- `METABASE_PASSWORD`: Metabase password (optional if using session token)
- `METABASE_SESSION_TOKEN`: Direct session token (optional)
- `METABASE_EMBED_SECRET`: Secret key for signed embedding

## API Endpoints

### Core Endpoints

- `POST /chat`: Main conversational interface
- `POST /plan`: Generate execution plan without running tools
- `GET /artifacts/{artifact_id}`: Download generated files
- `GET /health`: Health check
- `GET /info`: System configuration info
- `GET /docs`: Interactive API documentation

### Chat Request Format

```json
{
  "session_id": "unique-session-id",
  "user_id": "user-identifier", 
  "message": "Your natural language request"
}
```

### Chat Response Format

```json
{
  "message": "Response message",
  "preview_rows": [...],
  "artifacts": {
    "excel": {"artifact_id": "abc123", "download_url": "/artifacts/abc123"}
  },
  "embed_urls": ["https://metabase.example.com/embed/dashboard/..."],
  "plan": {...},
  "schema_catalog": {...},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Available Tools

### Data Operations
- **mongo.read**: Query MongoDB collections with aggregation pipelines
- **df.op**: DataFrame operations (select, filter, sort, groupby, pivot)
- **plot**: Generate charts (bar, line, pie, scatter)
- **excel**: Export DataFrames to Excel with auto-formatting

### CRM Actions
- **crm.create_task**: Create new tasks
- **crm.create_note**: Add notes to leads
- **crm.log_call**: Log phone calls
- **crm.create_activity**: Track activities
- **crm.update_lead**: Update lead information

### Metabase Integration
- **metabase.query**: Query Metabase cards and get DataFrames
- **metabase.embed**: Generate signed embed URLs for dashboards/questions

### Report Builder
- **report.build**: Create multi-sheet Excel reports combining MongoDB and Metabase data

## Example Usage

### 1. Analytics Query
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "analytics_session",
    "user_id": "analyst",
    "message": "Show me leads grouped by owner with total amounts, export to Excel"
  }'
```

### 2. Metabase Dashboard Embed
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "dashboard_session", 
    "user_id": "manager",
    "message": "Show me the sales performance dashboard from Metabase as an embed"
  }'
```

### 3. Multi-source Report
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "report_session",
    "user_id": "admin", 
    "message": "Build a weekly pipeline report with Metabase data and MongoDB leads"
  }'
```

## MongoDB Schema Examples

The system expects these collections in your MongoDB:

### leads
```json
{
  "_id": "ObjectId",
  "name": "John Doe",
  "email": "john@example.com",
  "status": "Qualified",
  "owner": "alice",
  "amount": 50000,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### tasks
```json
{
  "_id": "ObjectId",
  "title": "Follow up call",
  "due_date": "2024-01-15",
  "lead_id": "lead_id_here",
  "owner_id": "alice",
  "priority": "high",
  "completed": false
}
```

### notes
```json
{
  "_id": "ObjectId",
  "lead_id": "lead_id_here",
  "body": "Customer interested in enterprise plan",
  "created_at": "2024-01-01T00:00:00Z",
  "author": "alice"
}
```

## Security & RBAC

- **Collection Access**: Users can only access collections listed in `ALLOWED_COLLECTIONS`
- **Field Restrictions**: Sensitive fields (SSN, salary) are automatically filtered
- **Role-based Access**: Admin users (`admin`, `alice`) have elevated permissions
- **Pipeline Security**: Dangerous MongoDB operations (`$where`, `$function`) are blocked

## Development

### Running in Development Mode
```bash
uvicorn crm_agent_full:app --reload --host 0.0.0.0 --port 8000
```

### Testing with curl
```bash
# Health check
curl http://localhost:8000/health

# System info
curl http://localhost:8000/info

# Interactive docs
open http://localhost:8000/docs
```

## Architecture

This is a single-file application designed for clarity and ease of deployment. In production, consider:

- Splitting into modules (`models/`, `services/`, `api/`)
- Adding persistent conversation storage (Redis, PostgreSQL)
- Implementing proper authentication and authorization
- Adding comprehensive error handling and logging
- Setting up monitoring and metrics
- Adding rate limiting and request validation

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Verify `MONGO_URI` is correct
   - Ensure MongoDB is running and accessible
   - Check firewall and network settings

2. **Metabase Integration Issues**
   - Verify `METABASE_SITE_URL` is accessible
   - Check username/password or session token
   - Ensure embed secret is configured for signed embedding

3. **Swagger/OpenAPI Issues**
   - Verify `SWAGGER_SPEC_URL` returns valid JSON
   - Check authentication headers and tokens
   - Ensure API endpoints match the specification

4. **LLM Provider Issues**
   - For OpenAI: verify `OPENAI_API_KEY` is valid
   - For development: use `LLM_PROVIDER=json_stub`

### Logs and Debugging

The application logs to stdout with INFO level by default. Key events logged:
- Tool execution and errors
- Metabase authentication attempts
- Swagger client initialization
- Plan generation and execution

For more verbose logging, set the log level to DEBUG in the application.

