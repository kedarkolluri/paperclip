# Paperclip Python Server

Python replica of the Paperclip AI Agent Management Platform backend.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL (asyncpg) |
| **Validation** | Pydantic v2 |
| **Auth** | JWT (python-jose) + API keys |
| **Realtime** | WebSocket (native FastAPI) |
| **Storage** | Local disk / S3 (boto3) |
| **Encryption** | AES-256-GCM (cryptography) |
| **CLI** | Click + Rich |
| **Testing** | pytest + pytest-asyncio |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run database migrations
paperclip db-migrate

# Start development server
paperclip dev

# Or start production server
paperclip run
```

## Project Structure

```
python-server/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Configuration (env + file)
│   ├── database.py          # Async DB session management
│   ├── models/              # SQLAlchemy ORM models (34+ tables)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routes/              # FastAPI route handlers
│   ├── services/            # Business logic layer
│   ├── auth/                # JWT, API keys, actor resolution
│   ├── middleware/           # CSRF, error handling, hostname guard
│   ├── realtime/            # WebSocket live events
│   ├── storage/             # File storage (local/S3)
│   ├── secrets/             # AES-256-GCM encryption
│   ├── adapters/            # Agent execution adapters
│   └── cli/                 # Click CLI tool
├── pyproject.toml
├── Dockerfile
└── alembic.ini
```

## API Endpoints

All routes are mounted under `/api/`:

- `GET /api/health` – Health check
- `/api/companies` – Company CRUD
- `/api/agents` – Agent management, config revisions, API keys
- `/api/issues` – Issue CRUD, comments, labels, attachments
- `/api/projects` – Project & workspace management
- `/api/goals` – Goal management
- `/api/approvals` – Approval workflows
- `/api/costs` – Cost tracking & budgets
- `/api/activity` – Activity logging
- `/api/dashboard` – Dashboard summaries
- `/api/secrets` – Secret management
- `/api/assets` – File upload/download
- `/api/invites` – Invite & join request management
- `WS /api/companies/{id}/events/ws` – Live events

## CLI Commands

```bash
paperclip run                    # Start server
paperclip dev                    # Dev mode with reload
paperclip doctor                 # Diagnostic checks
paperclip configure KEY VALUE    # Set config
paperclip db-migrate             # Run migrations
paperclip company list           # List companies
paperclip agent list COMPANY_ID  # List agents
paperclip agent wakeup AGENT_ID  # Wake agent
paperclip issue list COMPANY_ID  # List issues
paperclip issue create CID TITLE # Create issue
paperclip dashboard COMPANY_ID   # Show dashboard
paperclip auth bootstrap-ceo     # Generate admin invite
```

## Configuration

Configuration is loaded from environment variables (`PAPERCLIP_*` prefix) and/or `~/.paperclip/config.json`.

Key settings:
- `PAPERCLIP_DEPLOYMENT_MODE`: `local_trusted` or `authenticated`
- `PAPERCLIP_DB_URL`: PostgreSQL connection string
- `PAPERCLIP_STORAGE_PROVIDER`: `local_disk` or `s3`
- `PAPERCLIP_SECRETS_PROVIDER`: `local_encrypted`
- `PAPERCLIP_AUTH_JWT_SECRET`: JWT signing secret
