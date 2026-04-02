# UniConnect Backend

FastAPI backend for UniConnect.

## Setup

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Database

This backend expects **Supabase Postgres**.

Set `DATABASE_URL` in `.env` to the direct SQLAlchemy-compatible Supabase Postgres URL, for example:

```bash
DATABASE_URL=postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

Then run migrations:

```bash
alembic upgrade head
```

Health check:

```bash
curl http://localhost:8000/api/health
```
