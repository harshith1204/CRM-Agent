# CRM Agent Makefile
# Convenient commands for development and deployment

.PHONY: help install setup dev test clean docker build deploy

help: ## Show this help message
	@echo "CRM Agent Development Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

setup: install ## Setup environment and MongoDB data
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please configure it"; fi
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@echo "Setting up MongoDB data..."
	@python setup_mongodb.py

dev: ## Start development server
	uvicorn crm_agent_full:app --reload --host 0.0.0.0 --port 8000

test: ## Run test examples
	python test_examples.py

clean: ## Clean up generated files and cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete

# Docker commands
docker-build: ## Build Docker image
	docker build -t crm-agent .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-stop: ## Stop Docker containers
	docker-compose down

docker-clean: ## Clean Docker containers and volumes
	docker-compose down -v
	docker system prune -f

# Development helpers
lint: ## Run code linting
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 crm_agent_full.py setup_mongodb.py test_examples.py; \
	else \
		echo "flake8 not installed. Install with: pip install flake8"; \
	fi

format: ## Format code with black
	@if command -v black >/dev/null 2>&1; then \
		black crm_agent_full.py setup_mongodb.py test_examples.py; \
	else \
		echo "black not installed. Install with: pip install black"; \
	fi

check: lint ## Run all checks
	@echo "✅ Code checks completed"

# MongoDB helpers
mongo-start: ## Start MongoDB with Docker
	docker run -d --name crm_mongodb -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password mongo:7.0

mongo-stop: ## Stop MongoDB container
	docker stop crm_mongodb && docker rm crm_mongodb

mongo-shell: ## Connect to MongoDB shell
	@if command -v mongosh >/dev/null 2>&1; then \
		mongosh mongodb://localhost:27017/crm; \
	else \
		docker exec -it crm_mongodb mongosh mongodb://localhost:27017/crm; \
	fi

# Production deployment
build: clean ## Build for production
	@echo "Building for production..."
	@pip install -r requirements.txt
	@python -m py_compile crm_agent_full.py
	@echo "✅ Build completed"

deploy: build ## Deploy to production (customize for your environment)
	@echo "🚀 Deploying to production..."
	@echo "Customize this target for your deployment environment"
	# Example: rsync, docker push, kubectl apply, etc.

# Quick start
quickstart: ## Complete setup and start development server
	@echo "🚀 CRM Agent Quick Start"
	@echo "======================="
	@$(MAKE) setup
	@echo ""
	@echo "🎯 Starting development server..."
	@$(MAKE) dev

# Documentation
docs: ## Generate and serve documentation
	@echo "📚 API documentation available at:"
	@echo "   http://localhost:8000/docs (Swagger UI)"
	@echo "   http://localhost:8000/redoc (ReDoc)"

# Environment validation
validate-env: ## Validate environment configuration
	@echo "🔍 Validating environment..."
	@python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['MONGO_URI', 'MONGO_DB']
optional = ['METABASE_SITE_URL', 'SWAGGER_BASE_URL', 'OPENAI_API_KEY']

print('Required variables:')
for var in required:
    value = os.getenv(var)
    status = '✅' if value else '❌'
    print(f'  {status} {var}: {value or \"NOT SET\"}')

print('\nOptional variables:')
for var in optional:
    value = os.getenv(var)
    status = '✅' if value else '⚠️ '
    print(f'  {status} {var}: {\"SET\" if value else \"NOT SET\"}')
"

# Database operations
db-reset: ## Reset database with fresh sample data
	@echo "⚠️  This will delete all existing data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@python -c "
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client[os.getenv('MONGO_DB', 'crm')]
for collection in ['leads', 'tasks', 'notes', 'call_logs', 'activity']:
    db[collection].delete_many({})
    print(f'Cleared {collection}')
"
	@python setup_mongodb.py

db-backup: ## Backup database to JSON files
	@echo "💾 Backing up database..."
	@mkdir -p backup
	@python -c "
import json
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client[os.getenv('MONGO_DB', 'crm')]

for collection_name in ['leads', 'tasks', 'notes', 'call_logs', 'activity']:
    docs = list(db[collection_name].find())
    for doc in docs:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
    
    filename = f'backup/{collection_name}_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
    with open(filename, 'w') as f:
        json.dump(docs, f, indent=2, default=str)
    print(f'Backed up {len(docs)} documents to {filename}')
"

# Show current status
status: ## Show current system status
	@echo "📊 CRM Agent Status"
	@echo "=================="
	@echo "Environment:"
	@$(MAKE) validate-env
	@echo ""
	@echo "Services:"
	@if curl -s http://localhost:8000/health >/dev/null 2>&1; then \
		echo "  ✅ CRM Agent API: Running on http://localhost:8000"; \
		curl -s http://localhost:8000/info | python -m json.tool; \
	else \
		echo "  ❌ CRM Agent API: Not running"; \
	fi
