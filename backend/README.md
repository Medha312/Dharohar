# Dharohar backend

Python + FastAPI backend for land-record digitization.

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`.

## PostgreSQL and Redis

Preferred: Docker Compose from the repository root (install Docker Desktop if `docker` is not on PATH):

```powershell
docker compose up -d
```

If you use a local PostgreSQL instance instead, create databases `dharohar` and `dharohar_test`, then set `DATABASE_URL` and `TEST_DATABASE_URL` in `backend/.env`.

Apply migrations:

```powershell
cd backend
alembic upgrade head
```

## Run the API

```powershell
cd backend
uvicorn app.main:app --reload
```

- `GET /`
- `GET /api/v1/health`
- Swagger: `/docs`

## Tests

```powershell
cd backend
pytest
```

Database tests expect PostgreSQL (`dharohar_test`) from Docker Compose.
