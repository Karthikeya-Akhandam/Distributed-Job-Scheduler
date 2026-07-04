# Design Decisions log — Architectural Trade-offs

This log details design constraints, tech stack selections, and structural compromises made during the design phase.

## 1. Custom Worker vs Celery/Pika
- **Selection**: Custom worker process polling PostgreSQL.
- **Trade-off**: Developing a polling layer introduces complexity (heartbeats, atomic lock contentions), but it demonstrates deep database transactional locking expertise (`SKIP LOCKED`) and gives us fine-grained control over executor pipelines without rabbitmq dependencies.

## 2. PostgreSQL `SKIP LOCKED` vs Redis queues
- **Selection**: PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` for task claiming.
- **Trade-off**: Redis-based lists (via bullmq or custom rpop) have lower latency. However, SQL claiming lets us use database transactional boundaries. If a worker goes offline mid-execution, we can detect stale heartbeats and safely reschedule the job using pure SQL transactions, ensuring high reliability.

## 3. Distributed Locking Layer
- **Selection**: PostgreSQL advisory locks (`pg_try_advisory_xact_lock`).
- **Trade-off**: Redis Redlock is widely used for distributed locking. However, advisory locks let us bind locks to PostgreSQL transaction lifetimes. If a connection drops, the lock is automatically released, preventing deadlock states.

## 4. Google Gemini for DLQ Analysis
- **Selection**: Gemini API with a local mock fallback.
- **Trade-off**: Sending every stack trace to Gemini is expensive. We mitigate this by only generating summaries when a user inspects a DLQ item on the frontend. The resulting analysis is then cached in the database.
