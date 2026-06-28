# Real-Time Analytics & Reporting Platform

A production-grade, secure, multi-tenant SaaS analytics platform designed to ingest high-throughput telemetry events, process them asynchronously, and visualize aggregated metrics through real-time dashboards.

---

## Technical Specifications

### Backend (Python)
- **Framework**: FastAPI (Asynchronous endpoints and dependency injection)
- **Database**: PostgreSQL with SQLAlchemy 2.0 (Eager relationships and async pg driver)
- **Database Migrations**: Alembic (Configured for async database operations)
- **Task Queue**: Celery + Redis (Asynchronous background parsing and periodic evaluations)
- **Scheduler**: Celery Beat (Evaluates alerting thresholds periodically)
- **Security**: JWT session access tokens + secure HTTP-only refresh cookies, SHA256 hashed API Keys, and Bcrypt password hashing.

### Frontend (React/TypeScript)
- **Framework**: Next.js 14 (App Router layout tree)
- **State Management**: Zustand (Client session store memory)
- **Caching**: TanStack Query (Query client state-caching and background refetching)
- **Visualizations**: Recharts (SSR-safe SVG charts: Line, Bar, Pie, KPI, and Tables)
- **Styling**: Tailwind CSS (Utility-first styling grid)

---

## Architectural & Security Highlights

1. **Strict Multi-Tenant Isolation**: Database tables use UUIDv4 primary keys to prevent IDOR and resource enumeration attacks. Every CRUD query and analytical aggregation filters records explicitly by the authenticated user's `organization_id`.
2. **Asynchronous Ingestion Worker**: To prevent database writes from blocking the main API thread, the single, batch, and CSV ingestion routes validate schemas and instantly delegate payloads to a Redis broker queue, returning an immediate `202 Accepted` response.
3. **NullPool Connection Worker Management**: Celery tasks run inside short-lived asyncio event loops. To prevent database connection pool exhaustion and `RuntimeError: Event loop is closed` errors, the Celery daemon is configured with a dedicated SQLAlchemy engine utilizing `NullPool`.
4. **CORS Explicit Security**: In compliance with the W3C CORS specification, wildcard `*` origins are blocked when credentials/cookies are active. The FastAPI app enforces explicit local origin mapping (`localhost`/`127.0.0.1`) to permit secure cookie transfers.
5. **Secure Session Recovery**: On page reload, the client Zustand store is populated silently by a background `/refresh` request. If a valid HttpOnly `refresh_token` cookie is present, the user session is restored without forcing another login.

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Backend Configurations
ENVIRONMENT=local
PROJECT_NAME="Real-Time Analytics Platform"
API_V1_STR=/api/v1

# PostgreSQL Async Connection string
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/analytics

# Redis Connection string (used by Celery & Beat)
REDIS_URL=redis://localhost:6379/0

# Security Configurations
JWT_SECRET_KEY=supersecuresecretkeychangeinproductionfortenantisolation
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7