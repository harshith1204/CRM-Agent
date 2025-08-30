# CRM Agent - Full-Stack Application

A comprehensive CRM Agent with conversational AI, analytics, and reporting capabilities. This application consists of a FastAPI backend with MongoDB integration and a modern React frontend.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup and startup script
./start_crm_agent.sh
```

This script will:
- Check and start MongoDB
- Install all dependencies
- Initialize the database with sample data
- Start both backend and frontend servers
- Provide access URLs

### Option 2: Manual Setup

#### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (local or Docker)

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database with sample data
python setup_full_stack.py

# Start the backend server
python crm_agent_full.py
# OR
# uvicorn crm_agent_full:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

## 📱 Application Features

### 🏠 Dashboard
- **Real-time KPIs**: MTD Revenue, New Leads, Win Rate, Average Cycle Time
- **Quick Actions**: Pre-built prompts for common tasks
- **Recent Artifacts**: Quick access to generated reports and charts

### 🤖 Agent Console  
- **Conversational AI**: Natural language queries for CRM data
- **Plan Visualization**: See how the agent breaks down and executes tasks
- **Artifact Generation**: Automatic creation of charts, reports, and exports
- **Real-time Execution**: Live updates as the agent processes requests

### 📊 Data Explorer
- **Multi-collection Browsing**: Explore leads, tasks, notes, and activities
- **Advanced Filtering**: Filter by owner, stage, and search terms
- **Export Capabilities**: Download data as Excel or CSV
- **Pagination**: Handle large datasets efficiently

### 📈 Report Builder
- **Saved Reports**: Create and manage reusable reports
- **Scheduled Execution**: Set up automated report generation
- **Multi-sheet Reports**: Combine data from MongoDB and Metabase
- **One-click Execution**: Generate reports on demand

## 🔧 API Endpoints

### Core Chat & Planning
- `POST /chat` - Send messages to the conversational agent
- `POST /plan` - Get execution plan without running tools

### Dashboard & Analytics
- `GET /kpis` - Get real-time KPI metrics
- `POST /data/explore` - Browse and filter CRM data
- `GET /data/export/{collection}` - Export collection data

### Report Management
- `GET /reports` - List all saved reports
- `POST /reports` - Create new report
- `GET /reports/{id}` - Get specific report
- `POST /reports/{id}/run` - Execute report
- `DELETE /reports/{id}` - Delete report

### Session Management
- `GET /sessions` - List chat sessions
- `GET /sessions/{id}/messages` - Get session messages
- `DELETE /sessions/{id}` - Delete session

### Utilities
- `GET /health` - Health check
- `GET /info` - System information
- `GET /collections/{name}/schema` - Collection schema info
- `GET /artifacts` - List all artifacts
- `GET /artifacts/{id}` - Download artifact

## 🛠️ Configuration

### Backend Environment Variables

```bash
# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB=crm
ALLOWED_COLLECTIONS=leads,tasks,notes,call_logs,activity

# LLM Provider
LLM_PROVIDER=json_stub  # or 'openai' for real AI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Metabase Integration (Optional)
METABASE_SITE_URL=https://your-metabase.com
METABASE_USERNAME=user@example.com
METABASE_PASSWORD=password
METABASE_EMBED_SECRET=your-embed-secret

# External CRM Integration (Optional)
SWAGGER_SPEC_URL=https://your-crm.com/swagger.json
SWAGGER_BASE_URL=https://your-crm.com
SWAGGER_AUTH_HEADER=Authorization
SWAGGER_AUTH_VALUE=Bearer YOUR_TOKEN
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_DEV_MODE=true
```

## 📋 Sample Prompts

Try these conversational prompts in the Agent Console:

- **Analytics**: "Deals created last week by owner (bar chart)"
- **Export**: "Leads with no activity in 14 days (export)"
- **Revenue**: "MTD revenue vs target by region"
- **Pipeline**: "Pipeline forecast for next quarter"
- **Tasks**: "Create follow-up tasks for stale leads"

## 🏗️ Architecture

### Backend (FastAPI + MongoDB)
- **Conversational AI**: Plan-Act-Observe loop with session memory
- **Data Layer**: MongoDB with RBAC and field-level security
- **Analytics Engine**: Pandas + Matplotlib for data processing
- **Export Engine**: Excel/CSV generation with custom formatting
- **Metabase Integration**: Signed embedding and API queries
- **CRM Integration**: Swagger-based external system integration

### Frontend (React + TypeScript)
- **Modern UI**: Tailwind CSS with shadcn/ui components
- **Real-time Updates**: React Query for data fetching
- **Responsive Design**: Mobile-first approach
- **Type Safety**: Full TypeScript integration
- **State Management**: React hooks and context

### Data Flow
1. **User Input** → Frontend captures user interactions
2. **API Calls** → Frontend calls backend REST APIs
3. **AI Processing** → Backend uses LLM to plan actions
4. **Tool Execution** → Backend executes MongoDB queries, generates charts/reports
5. **Response** → Results sent back to frontend with artifacts
6. **UI Updates** → Frontend displays results, charts, and download links

## 🔒 Security Features

- **RBAC**: Role-based access control for collections
- **Field-level Security**: Sensitive field filtering
- **Session Management**: Secure session handling
- **Input Validation**: Pydantic models for all inputs
- **MongoDB Injection Protection**: Pipeline validation

## 🧪 Testing

### Backend Testing
```bash
# Run backend tests
python test_examples.py

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/kpis
```

### Frontend Testing
```bash
cd frontend
npm run lint
npm run build
```

## 📦 Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual containers
docker build -t crm-agent-backend .
docker build -t crm-agent-frontend ./frontend
```

### Environment Setup
- Set up production MongoDB cluster
- Configure LLM provider (OpenAI, etc.)
- Set up Metabase instance (optional)
- Configure external CRM integration (optional)
- Set up proper authentication and authorization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the sample data in `setup_full_stack.py`
- Check logs for debugging information

## 🎯 Roadmap

- [ ] Real-time notifications
- [ ] Advanced report scheduling
- [ ] Multi-tenant support
- [ ] Enhanced AI capabilities
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Integration marketplace