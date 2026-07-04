# REST API Specification Reference

This document highlights critical endpoints for client integrations. The full OpenAPI specifications are dynamically exposed on Swagger.

## Swagger Interface URLs
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc reference panel**: `http://localhost:8000/redoc`

## Primary API Endpoints

### 1. Authentication
- `POST /api/v1/auth/register`: Create user account.
- `POST /api/v1/auth/login`: Issue JWT token pair.
- `POST /api/v1/auth/refresh`: Refresh expired credentials.

### 2. Queue Configuration
- `POST /api/v1/projects/{project_id}/queues`: Create background queue.
- `POST /api/v1/queues/{queue_id}/pause`: Pause processing.
- `POST /api/v1/queues/{queue_id}/resume`: Resume processing.
- `GET /api/v1/queues/{queue_id}/stats`: Retrieve throughput metrics.

### 3. Job Dispatching
- `POST /api/v1/queues/{queue_id}/jobs`: Enqueue immediate, delayed, or cron job.
- `POST /api/v1/queues/{queue_id}/jobs/batch`: Enqueue a batch of jobs under a transaction.
- `POST /api/v1/jobs/{job_id}/retry`: Manually re-trigger a failed task.
- `GET /api/v1/jobs/{job_id}/logs`: Retrieve worker terminal outputs.

### 4. Dead Letter Queue
- `GET /api/v1/queues/{queue_id}/dlq`: List dead letter items.
- `GET /api/v1/dlq/{dlq_id}/ai-summary`: Trigger Google Gemini error stack root cause analysis.
- `POST /api/v1/dlq/{dlq_id}/retry`: Re-enqueue dead-letter item.
