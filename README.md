# University Application & Recommendation System

FastAPI backend providing university & program management plus a multi-source recommendation engine (MySQL + Neo4j).

## Core Capabilities
- Users, interests, programs, universities, regions, applications
- Dual-database sync (MySQL transactional + Neo4j graph)
- Qualification evaluation & recommendation scoring
- JWT auth-ready structure (extend as needed)
- Structured logging (see [LOGGING_README.md](LOGGING_README.md))
- Environment validation (see [ENV_CONFIG.md](ENV_CONFIG.md))

## Tech Stack
- Python 3.8+
- FastAPI / Pydantic
- MySQL (primary data store)
- Neo4j (graph relationships & recs)
- Uvicorn
- Logging with rotation (logs/app.log, logs/error.log, logs/debug.log)

## Quick Start
```bash
git clone <your-repo-url>
cd Backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill credentials
python -m app.main    # initializes & tests DB connections
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000

## Environment
Configure `.env` (see [ENV_CONFIG.md](ENV_CONFIG.md)) for:
- App settings (PORT, DEBUG, ENVIRONMENT)
- MySQL (host/user/password/db)
- Neo4j (uri/user/password)
- Optional logging overrides

## Data Flow Overview
MySQL stores authoritative entities. Neo4j mirrors selective data (users, programs, relationships) to enable:
- Interest-based matching
- Qualification relationships
- Similar program discovery

## Recommendation Engine (Combined Score)
Sources (weights configurable in code):
- Interests (e.g., declared interest relevance)
- Qualification status (meets or exceeds program requirements)
- Graph relationships (similarity + prior matches)

Enhancements:
- Boost for multi-source appearance
- Filters: location, tuition cap, language
- Stats + explanation endpoint

## Standard API Response
Success:
```json
{ "error": 0, "timestamp": "...", "message": "ok", "data": { ... } }
```
Failure:
```json
{ "detail": { "error": 404, "timestamp": "...", "message": "not found", "data": null } }
```

## Key Endpoint Groups (REST)
- Users: create/update/delete + recommendations
- Interests: CRUD + Neo4j sync
- Programs / Universities / Regions: CRUD + field & region filters
- Qualifications: check single/all, sync, summary, qualified users
- Recommendations: combined, per-source, similar, stats
(See route definitions in `app/routes/`.)

## Running Tests / Utilities
```bash
python tests/populate_neo4j.py   # seed sample graph data
# Add your own pytest suite as needed
```

## Logs
Rotated files in `/logs`:
- app.log (general)
- error.log (errors)
- debug.log (debug if enabled)

## Contributing
1. Branch: git checkout -b feat/short-description
2. Commit: git commit -m "#123 | feat: add X"
3. PR: submit for review

## License
MIT

## Support
Open an issue or contact maintainer.

---
For advanced logging: [LOGGING_README.md](LOGGING_README.md)  
For full env reference: