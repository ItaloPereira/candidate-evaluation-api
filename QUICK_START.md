# Quick Start

## Option A: Docker (Recommended)

```bash
./setup.sh
```

That's it. Open http://localhost:8000/docs to verify.

## Option B: Local Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Verify

- [ ] http://localhost:8000/docs shows Swagger UI
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] Tests pass: `pytest -v` (local) or `docker compose exec app pytest -v` (Docker)

## Useful Commands

| Command | Description |
|---------|-------------|
| `docker compose up` | Start the app |
| `docker compose down` | Stop the app |
| `docker compose exec app pytest -v` | Run tests |
| `docker compose exec app bash` | Shell into the container |
| `docker compose logs -f` | View logs |
