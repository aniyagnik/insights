# Real-Time Multi-Tenant Analytics & Reporting Platform

This is a full-stack, production-ready SaaS analytics tool. The application utilizes asynchronous Python architecture on the backend to handle high-throughput event ingestion, and a modern, state-cached Next.js 14 client on the frontend to visualize metrics in real-time.

---

## Architectural & Security Blueprint

### 1. Database Schema & Multi-Tenancy
* **Secure Identifiers**: All relational tables use UUIDv4 primary keys instead of sequential integers to mitigate IDOR (Insecure Direct Object Reference) and enumeration vectors.
* **Tenant-Level Isolation**: Every analytical query, dashboard fetch, and event logging execution is securely bound to the authenticated user's `organization_id` at the query layer.
* **Optimized Indexing**: The `events` table features composite indices (`ix_events_org_timestamp` and `ix_events_org_name_timestamp`) to ensure high-performance, low-latency chronological queries.

### 2. High-Throughput Event Ingestion
* **Asynchronous Ingest Pipeline**: REST ingestion endpoints (`/single`, `/batch`, `/csv`) validate schemas using Pydantic v2 and immediately delegate processing payloads to a Celery background queue, returning a `202 Accepted` status to the client.
* **Atomic Rate Limiter**: Implements an atomic sliding-window rate limiter per API Key inside Redis sorted sets (`zset`) to protect the ingestion pipeline from overload.

### 3. Session and Connection Management
* **Stateless Session Recovery**: Integrates short-lived JWT access tokens alongside long-lived refresh tokens stored inside secure, HTTP-only cookies. On browser refresh, the client silently restores the user session state.
* **Worker Connection Preservation**: The Celery background worker processes run in separate asyncio event loops. To avoid `RuntimeError: Event loop is closed` errors, the worker uses a dedicated database engine configured with `NullPool`.
* **CORS Constraints**: The FastAPI application restricts origin access to explicit development hostnames to allow secure cookie credentials sharing between the client and the API server.

---

## Workspace Directory Structure

```text
analytics-platform/
│
├── app/                          # Python FastAPI Backend Folder
│   ├── api/                      # Routing layers & Dependency Injection
│   ├── core/                     # Handlers, Security, WebSockets, & Config
│   ├── models/                   # SQLAlchemy 2.0 Database Models
│   ├── schemas/                  # Pydantic validation schemas
│   └── worker.py                 # Celery Tasks, Beat Scheduler, & Engines
│
├── frontend/                     # Next.js 14 Frontend Folder
│   ├── app/                      # Next.js App Router (Layout, Home, Dashboard)
│   ├── components/               # Reusable UI Elements, Providers, and Charts
│   ├── lib/                      # Type-safe Fetch API Client
│   └── store/                    # Zustand Global Auth State Store
│
├── alembic/                      # Alembic Database Migration scripts
├── requirements.txt              # Backend dependency mapping
└── README.md                     # Setup and instruction manual
```

---

## Prerequisites

Ensure the following packages are installed locally:

* Python 3.11+
* Node.js 18+
* Docker (for PostgreSQL and Redis containers)
---

## Setup & Running Instructions

### Step 1: Run Infrastructure (Docker)

We use Docker to run PostgreSQL and Redis containers. Open your terminal and run:

```bash
# Start PostgreSQL (port 5432)
docker run --name local-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=analytics \
  -p 5432:5432 -d postgres:15

# Start Redis Broker (port 6379)
docker run --name local-redis \
  -p 6379:6379 -d redis:7
```

### Step 2: Configure and Migrate the Backend

1. Navigate to the project root directory and set up your Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```


2. Install Python dependencies:
```bash
pip install -r requirements.txt
```


3. Create your `.env` configuration file in the project root folder:
```env
ENVIRONMENT=local
PROJECT_NAME="Real-Time Analytics Platform"
API_V1_STR=/api/v1
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/analytics
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=supersecuresecretkeychangeinproductionfortenantisolation
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

4. Apply database migrations to provision tables (Users, Orgs, Events, Dashboards, Widgets, Invites, Alerts):
```bash
alembic upgrade head
```



### Step 3: Run Backend Services

You will need to open two separate terminal tabs to run the API server and the background worker.

#### Terminal 1: FastAPI API Server

Ensure your virtual environment is active in this terminal, and run:

```bash
uvicorn app.main:app --reload --port 8000
```

* **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Terminal 2: Celery Worker & Beat Scheduler

Ensure your virtual environment is active in this terminal, and run:

```bash
celery -A app.worker.celery_app worker -B --loglevel=info
```

> **Note:** The `-B` flag tells Celery to run both the task worker and the periodic alerting scheduler together in a single loop lifecycle.

### Step 4: Configure and Run the Frontend

Open a third terminal tab to set up and run the Next.js frontend client:

1. Navigate to the frontend directory:
```bash
cd frontend
```


2. Install Node.js packages:
```bash
npm install
```


3. Run the development server:
```bash
npm run dev
```



* **Frontend Access:** [http://127.0.0.1:3000](http://127.0.0.1:3000)

> [!IMPORTANT]
> **CRITICAL DEVELOPER NOTE:** To allow secure, `HttpOnly` cookie sharing between your frontend and backend locally, always access the frontend on the raw IP **http://127.0.0.1:3000** instead of `http://localhost:3000`. This ensures the hostnames align exactly with your backend URL (http://127.0.0.1:8000), allowing the browser to classify cookie transactions as `Same-Site`.
---

## End-to-End Verification Guide

To test the entire integrated loop from scratch:

### 1. Register and Log In

1. Go to [http://127.0.0.1:3000/](http://127.0.0.1:3000/) in your browser.
2. Since no session exists, you will see the unified Sign-In page.
3. Sign up an administrative owner account or log in if you have registered one. Once authenticated, you will be redirected to the `/dashboard` workspace.

### 2. Generate an Ingestion API Key

1. In Swagger UI ([http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)), authenticate yourself using your login credentials.
2. Send a `POST` request to `/api/v1/api-keys/` with payload `{"name": "Client Server"}`.
3. Copy the returning plain text key (e.g., `pk_live_xxxx...`).

### 3. Ingest Telemetry Data

Send a tracking event via curl:

```bash
curl -X POST "[http://127.0.0.1:8000/api/v1/ingest/single](http://127.0.0.1:8000/api/v1/ingest/single)" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_PLAIN_TEXT_KEY_HERE" \
     -d '{
       "event_name": "page_view",
       "properties": {
         "url": "/pricing",
         "browser": "Firefox"
       }
     }'
```

Verify that the endpoint returns `202 Accepted` immediately and your active Celery worker log prints the success confirmation.

### 4. Create a Widget and View Recharts Graphs

1. Go to Swagger UI and create a dashboard under `/api/v1/dashboards/`. Save the dashboard id.
2. Create a widget inside that dashboard via `POST /api/v1/dashboards/{dashboard_id}/widgets` with payload:
```json
{
  "name": "Live Page Views",
  "type": "line",
  "query_config": {
    "event_name": "page_view",
    "time_range_hours": 24,
    "interval": "hour"
  }
}
```


3. Refresh your Next.js frontend workspace page ([http://127.0.0.1:3000/dashboard](http://127.0.0.1:3000/dashboard)).
4. Select your dashboard. Confirm that your Recharts line graph successfully renders your ingested page views.

### 5. Open Real-Time WebSocket Log Stream

1. In your frontend `/dashboard` page, click on the **Live Stream Viewer** tab in the top right.
2. Ingest another single or CSV tracking payload via your terminal.
3. Observe the frontend console. The incoming event payload will instantly print itself onto the terminal logging stream without requiring any page reloads.