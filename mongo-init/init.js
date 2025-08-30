// MongoDB initialization script for Docker
// This script runs when the MongoDB container starts for the first time

// Switch to the CRM database
db = db.getSiblingDB('crm');

// Create collections with validation schemas
db.createCollection('leads', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'email', 'status', 'owner'],
      properties: {
        name: { bsonType: 'string' },
        email: { bsonType: 'string' },
        status: { 
          bsonType: 'string',
          enum: ['New', 'Contacted', 'Qualified', 'Proposal', 'Closed Won', 'Closed Lost']
        },
        owner: { bsonType: 'string' },
        amount: { bsonType: 'number', minimum: 0 },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('tasks', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'owner_id'],
      properties: {
        title: { bsonType: 'string' },
        owner_id: { bsonType: 'string' },
        priority: {
          bsonType: 'string',
          enum: ['low', 'medium', 'high', 'urgent']
        },
        status: {
          bsonType: 'string', 
          enum: ['open', 'in_progress', 'completed', 'cancelled']
        },
        completed: { bsonType: 'bool' }
      }
    }
  }
});

db.createCollection('notes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['lead_id', 'body', 'author'],
      properties: {
        lead_id: { bsonType: 'string' },
        body: { bsonType: 'string' },
        author: { bsonType: 'string' },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('call_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['lead_id', 'direction'],
      properties: {
        lead_id: { bsonType: 'string' },
        direction: {
          bsonType: 'string',
          enum: ['inbound', 'outbound']
        },
        duration_seconds: { bsonType: 'number', minimum: 0 },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('activity', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['lead_id', 'type'],
      properties: {
        lead_id: { bsonType: 'string' },
        type: {
          bsonType: 'string',
          enum: ['email', 'meeting', 'demo', 'followup', 'call']
        },
        when: { bsonType: 'date' },
        owner: { bsonType: 'string' }
      }
    }
  }
});

// Create indexes for better performance
db.leads.createIndex({ "owner": 1, "status": 1 });
db.leads.createIndex({ "created_at": -1 });
db.leads.createIndex({ "amount": -1 });
db.leads.createIndex({ "email": 1 }, { unique: true });

db.tasks.createIndex({ "owner_id": 1, "due_date": 1 });
db.tasks.createIndex({ "lead_id": 1 });
db.tasks.createIndex({ "status": 1 });

db.notes.createIndex({ "lead_id": 1, "created_at": -1 });
db.notes.createIndex({ "author": 1 });

db.call_logs.createIndex({ "lead_id": 1, "created_at": -1 });
db.call_logs.createIndex({ "direction": 1 });

db.activity.createIndex({ "lead_id": 1, "when": -1 });
db.activity.createIndex({ "type": 1 });
db.activity.createIndex({ "owner": 1 });

print("✅ CRM database initialized with collections, validation, and indexes");
