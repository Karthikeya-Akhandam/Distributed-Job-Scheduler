# System Architecture — Distributed Job Scheduler

This document details the software architecture, communications flow, and structural topologies of the background scheduler platform.

## Architecture Topology

```
                   ┌───────────────────────┐
                   │    Next.js Client     │
                   │  (React Dashboard UI) │
                   └───────────┬───────────┘
                               │ (REST & WebSockets)
                               ▼
                   ┌───────────────────────┐
                   │  FastAPI Backend API  │◀──────────────┐
                   │ (HTTP / WS Webserver) │               │
                   └───────────┬───────────┘               │
                               │                           │
         ┌─────────────────────┴─────────────────────┐     │
         ▼                                           ▼     │
┌─────────────────┐                         ┌─────────────────┐
│  PostgreSQL DB  │                         │   Redis Cache   │
│ (State / Locks) │                         │ (Events PubSub) │
└────────▲────────┘                         └────────▲────────┘
         │                                           │
         │ (Poll SQL / Claim Locks)                  │ (Publish Event)
         └─────────────────────┬─────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   │ Python Worker Daemon  │
                   │ (asyncio Task Group)  │
                   └───────────────────────┘
```

## System Components

### 1. Backend REST & WebSocket Gateway
- **Technology**: FastAPI (Python), ASGI Web Server, Pydantic, SQLAlchemy Async.
- **Role**: Validates parameters, manages authentication boundaries, serves stats API queries, registers worker nodes, and pushes real-time queue notifications through WebSockets to clients.

### 2. Relational Database Engine
- **Technology**: PostgreSQL 16.
- **Role**: Serves as the central persistent authority. Manages transactional boundaries. Queued jobs, retry strategies, system auditing, and dead-letter records live here.

### 3. Redis Telemetry Pub/Sub broker
- **Technology**: Redis.
- **Role**: Emits real-time event notifications. Active worker state updates and job transitions get published to Redis, which the WebSocket server forwards reactively.

### 4. Custom Python Worker Daemon
- **Technology**: Python, asyncio, psutil.
- **Role**: Polls PostgreSQL atomically using advisory locks and transaction markers. Executes tasks concurrently, schedules failures/retries, and reports periodic CPU/memory heartbeats.
