# Distributed Job Scheduler

A production-inspired distributed job scheduling platform capable of reliably executing asynchronous background jobs across multiple workers.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js        │     │   FastAPI        │     │   Worker        │
│   Dashboard      │────▶│   Backend        │◀────│   Service(s)    │
│   (Frontend)     │     │   (REST + WS)    │     │   (Python)      │
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                         │
                         ┌───────┴───────┐                 │
                         │               │                 │
                    ┌────▼────┐   ┌──────▼──┐              │
                    │PostgreSQL│   │  Redis   │◀────────────┘
                    │  (Data)  │   │(Pub/Sub) │
                    └─────────┘   └─────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python, FastAPI, SQLAlchemy, Alembic |
| Worker Service | Python, asyncio, custom job claimer |
| Frontend | Next.js 15, React, TailwindCSS, Recharts |
| Database | PostgreSQL 16 |
| Cache / Pub-Sub | Redis 7 |
| Containerization | Docker, Docker Compose |
| AI Summaries | Google Gemini API (configurable) |

## Features

### Core
- 🔐 JWT Authentication with refresh tokens
- 🏢 Organization & project management
- 📋 Queue management (priority, concurrency, pause/resume)
- 📦 Job types: immediate, delayed, scheduled, recurring (cron), batch
- ⚙️ Worker service with atomic job claiming (`SELECT FOR UPDATE SKIP LOCKED`)
- 🔄 Configurable retry strategies (fixed, linear, exponential backoff)
- 💀 Dead Letter Queue with manual retry/discard
- 📊 Execution logs, metrics, and worker monitoring

### Bonus
- 🔗 Workflow dependencies (Job DAGs)
- 🚦 Rate limiting (token bucket)
- 🔒 Distributed locking (PostgreSQL advisory locks)
- 🧩 Queue sharding
- ⚡ Event-driven execution (Redis Pub/Sub)
- 🔴 WebSocket live updates
- 👥 Role-based access control (RBAC)
- 🤖 AI-generated failure summaries (Gemini)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd distributed-job-scheduler

# 2. Copy environment variables
cp .env.example .env

# 3. Start infrastructure (PostgreSQL + Redis)
make db-up

# 4. Run database migrations
make migrate

# 5. Seed demo data (optional)
make seed

# 6. Start all services
make dev
```

### Individual Services

```bash
# Backend only (http://localhost:8000)
make dev-backend

# Frontend only (http://localhost:3000)
make dev-frontend

# Worker only
make dev-worker
```

### Running Tests

```bash
# All tests
make test

# Backend tests with coverage
make test-backend

# Worker tests
make test-worker
```

## Project Structure

```
distributed-job-scheduler/
├── backend/              # FastAPI REST API + WebSocket server
│   ├── app/
│   │   ├── api/          # Route handlers (v1)
│   │   ├── core/         # Security, middleware, events
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic layer
│   │   └── utils/        # Retry calculators, helpers
│   ├── alembic/          # Database migrations
│   └── tests/            # Backend tests
├── worker/               # Custom worker service
│   ├── app/
│   │   ├── handlers/     # Job type handlers
│   │   ├── claimer.py    # Atomic job claiming
│   │   ├── executor.py   # Concurrent execution
│   │   ├── heartbeat.py  # Health reporting
│   │   └── shutdown.py   # Graceful shutdown
│   └── tests/
├── frontend/             # Next.js dashboard
│   └── src/
│       ├── app/          # Pages (App Router)
│       ├── components/   # React components
│       ├── hooks/        # Custom hooks
│       └── lib/          # API client, types, utils
├── docs/                 # Architecture, ER diagram, API docs
├── docker-compose.yml    # Infrastructure orchestration
├── Makefile              # Developer commands
└── .env.example          # Environment template
```

## API Documentation

When the backend is running, interactive API docs are available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Documentation

- [System Architecture](docs/architecture.md)
- [ER Diagram](docs/er-diagram.md)
- [API Reference](docs/api-docs.md)
- [Design Decisions](docs/design-decisions.md)

## License

MIT
