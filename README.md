# Resource Storage Service

An API-only, production-ready FastAPI microservice acting as a centralized runtime storage layer for multiple FastAPI services. 
Uses a single JSON file (`data/resources.json`) for shared storage.

## Architecture

The service uses a thread-safe `StorageManager` with file locking to ensure multiple concurrent operations don't corrupt the JSON structure.

## Installation

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## Local Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Run

```bash
docker build -t resource-storage-service .
docker run -p 8000:8000 -v $(pwd)/data:/app/data --name resource-storage resource-storage-service
```

## Docker Compose Run

```bash
docker-compose up -d
```

## API Examples / cURL

### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```

### 2. Retrieve Entire Storage
```bash
curl -X GET http://localhost:8000/resources
```

### 3. Retrieve Table (e.g. tech_stack)
```bash
curl -X GET http://localhost:8000/tables/tech_stack
```

### 4. Update Entire Table (e.g. rate_card)
```bash
curl -X PUT http://localhost:8000/tables/rate_card/update \
  -H "Content-Type: application/json" \
  -d '[
  {
    "roles": {
      "project_manager": { "daily_rate_usd": 125 }
    },
    "financial_guidelines": {
      "standard_profit_margin_percentage": 25
    }
  }
]'
```

### 5. Retrieve File Content (e.g. company_profile.txt)
```bash
curl -X GET http://localhost:8000/files/company_profile.txt
```

### 6. Update Entire File (e.g. brand_guidelines.txt)
```bash
curl -X PUT http://localhost:8000/files/brand_guidelines.txt \
  -H "Content-Type: application/json" \
  -d '"1. Professional and Authoritative: Speak as an industry expert..."'
```
