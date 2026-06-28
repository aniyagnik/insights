# Real-Time Multi-Tenant Analytics & Reporting Platform

A production-grade, full-stack SaaS analytics tool. The application utilizes an asynchronous Python architecture on the backend to handle high-throughput event ingestion and periodic alerting, and a modern, state-cached Next.js 14 client on the frontend to visualize metrics in real-time.

---

## Architectural & Security Highlights

### 1. Database Schema & Multi-Tenancy
* **Secure Identifiers**: All relational tables use UUIDv4 primary keys instead of sequential integers to mitigate IDOR (Insecure Direct Object Reference) and resource enumeration attacks.
* **Tenant-Level Isolation**: Every analytical query, dashboard fetch, and event logging execution is securely bound to the authenticated user's `organization_id` at the query layer.
* **Optimized Indexing**: The `events` table features composite indices (`ix_events_org_timestamp` and `ix_events_org_name_timestamp`) to ensure high-performance, low-latency chronological queries.

### 2. High-Throughput Event Ingestion
* **Asynchronous Ingest Pipeline**: REST ingestion endpoints (`/single`, `/batch`, `/csv`) validate schemas using Pydantic v2 and immediately delegate processing payloads to a Celery background queue, returning a `202 Accepted` status to the client.
* **Atomic Rate Limiter**: Implements an atomic sliding-window rate limiter per API Key inside Redis sorted sets (`zset`) to protect the ingestion pipeline from overload.

### 3. Session and Connection Management
* **Stateless Session Recovery**: Integrates short-lived JWT access tokens alongside long-lived refresh tokens stored inside secure, HTTP-only cookies. On browser refresh, the client silently restores the user session state.
* **Worker Connection Preservation**: The Celery background worker processes run in separate asyncio event loops. To avoid `RuntimeError: Event loop is closed` errors, the worker uses a dedicated database engine configured with `NullPool`.
* **CORS Constraints**: The FastAPI application restricts origin access to explicit development and production hostnames to allow secure cookie credentials sharing between the client and the API server.

---

## Workspace Directory Structure

```text
analytics-platform/
│
├── app/                          # Python FastAPI Backend Folder
│   ├── api/                      # Routing layers & Dependency Injection
│   ├── core/                     # Handlers, Security, WebSockets, & Exceptions
│   ├── models/                   # SQLAlchemy 2.0 Database Models
│   ├── schemas/                  # Pydantic validation schemas
│   └── worker.py                 # Celery Tasks, Beat Scheduler, & Engines
│
├── frontend/                     # Next.js 14 Frontend Folder
│   ├── app/                      # Next.js App Router (Layout, Home, Dashboard, Onboarding)
│   ├── components/               # Reusable UI Elements, Providers, and Charts
│   ├── lib/                      # Type-safe Fetch API Client
│   └── store/                    # Zustand Global Auth State Store
│
├── alembic/                      # Alembic Database Migration scripts
├── Dockerfile                    # Unified Dockerfile for container deployments
├── start.sh                      # Startup script for Render free tier multi-process runs
├── .gitignore                    # Local development git ignoring configuration
├── requirements.txt              # Backend dependency mapping
└── README.md                     # Setup and instruction manual
```

### Prerequisites

Ensure the following packages are installed locally:

* Python 3.11+
* Node.js 18+
* Docker (for PostgreSQL and Redis containers)
---

## Setup & Running Instructions (Local)

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

Navigate to the project root directory and set up your Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Create your `.env` configuration file in the project root folder:
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

Apply database migrations to provision tables (`Users`, `Orgs`, `Events`, `Dashboards`, `Widgets`, `Invites`, `Alerts`):

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

* **Interactive API Documentation**: http://127.0.0.1:8000/docs

#### Terminal 2: Celery Worker & Beat Scheduler

Ensure your virtual environment is active in this terminal, and run:

```bash
celery -A app.worker.celery_app worker -B --loglevel=info
```

> **Note**: The `-B` flag tells Celery to run both the task worker and the periodic alerting scheduler together in a single loop lifecycle.

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



* **Frontend Access**: http://127.0.0.1:3000

> [!IMPORTANT]
> **CRITICAL DEVELOPER NOTE**: To allow secure, `HttpOnly` cookie sharing between your frontend and backend locally, always access the frontend on the raw IP **http://127.0.0.1:3000** instead of `http://localhost:3000`. This ensures the hostnames align exactly with your backend URL (`http://127.0.0.1:8000`), allowing the browser to classify cookie transactions as `Same-Site`.

---

## Production Deployment Guide

We use Vercel to host our frontend and Render to host our backend services.

### 1. Backend Deployment (Render Free Tier)

Render's free tier does not support separate background workers. To bypass this, we use the root-level `start.sh` startup script to run database migrations, FastAPI, Celery Workers, and Celery Beat concurrently inside a single, free Web Service container.

1. Provision a free PostgreSQL instance on Render and a free Redis database on Upstash.
2. Create a new **Web Service** on Render, pointing to your GitHub repository:
* **Runtime**: `Docker`
* **Instance Type**: `Free`


3. Configure the following environment variables in the Render dashboard:
* `DATABASE_URL`: *YOUR_INTERNAL_RENDER_POSTGRESQL_CONNECTION_STRING*
* `REDIS_URL`: *YOUR_UPSTASH_REDIS_CONNECTION_STRING*
* `ENVIRONMENT`: `production`
* `JWT_SECRET_KEY`: *your_secure_production_secret_key*
* `PORT`: `8000`


4. Click **Create Web Service**. The container will boot up, automatically run `alembic upgrade head`, and start all background threads.

### 2. Frontend Deployment (Vercel)

1. Import your GitHub repository into Vercel.
2. Set the **Root Directory** to `frontend`.
3. Configure your Environment Variables:
* `NEXT_PUBLIC_API_URL`: Set to your public Render API URL: `https://YOUR_API_SUBDOMAIN.onrender.com/api/v1`


4. Click **Deploy**.

> [!IMPORTANT]
> **Production CORS Update**: After Vercel deploys, copy your production frontend URL (e.g., `https://your-app.vercel.app`) and append it to the `CORSMiddleware` configuration inside your backend's `app/main.py` to permit secure session cookie transfers in production.

---

## End-to-End Verification Guide (Testing via UI)

With our updated frontend panels, you no longer need Swagger or terminal curl scripts to test or demonstrate the application. Everything can be fully managed directly through your Next.js dashboard:

### 1. Register a New Organization & Sign In

* Open your browser and navigate to http://127.0.0.1:3000.
* Click **"New organization? Create Account"**.
* Enter your organization name, email, and password. Upon clicking submit, you will be registered on the backend, logged in automatically, and redirected to your `/dashboard` workspace.

### 2. Create Your Dashboard & Widgets

* On your empty dashboard view, click **"Create First Dashboard"**.
* Set the name to `Production Telemetry`, write an optional description, check **"Make Dashboard Public"** if you want to test public share links, and click **Create**.
* Click the blue **"+ Add Chart Widget"** button in the top right to configure a chart card:
* **Name**: `Pricing Signups`
* **Visualization**: Line Chart (or Bar, Pie, KPI, Table)
* **Target Tracking Event**: `pricing_completed` *(Note: database matching is case-sensitive!)*



### 3. Generate API Keys & Simulate Ingestion

* Go to the **Developer Settings** tab on your workspace navigation.
* Under **API Key Manager**, enter a key name and click **Generate**.
* Copy your plain-text key from the secure green warning banner. *(This key automatically populates your simulators)*.
* Under **Single Event Simulator**:
* Ensure your copied key is pasted in the auth field.
* Set the event name to `pricing_completed`.
* Click **Simulate & Ingest Event** 3 to 4 times.


* Under **Batch Event Simulator**:
* Paste an array of events with varied timestamps to test chronological trend lines.


* Switch back to your **Production Telemetry** tab. Refresh (or wait for the 30-second TanStack cache auto-refresh). Your Recharts graphs will render your active data points!

### 4. Open Real-Time WebSocket Log Stream

* Click on the **Live Stream** tab.
* Verify that the indicator dot glows emerald green and reads **Active**.
* Open a separate browser tab or window on **Developer Settings** and trigger a single or CSV ingestion event.
* Go back to the **Live Stream** tab. The event will instantly stream onto your terminal logging feed in real-time.

### 5. Onboard Team Members

* Go to the **Team & Alerts** tab.
* Under **Team Onboarding**, type a colleague's email, assign them a role, and click send.
* Double-click the generated registration link under "Pending Invites" to copy it.
* Open an Incognito window, paste the URL, type a password, and join the workspace!