# Candidate Evaluation API - Technical Assessment

Welcome! This is a **2-hour technical assessment** (15 min briefing + **75 min coding** + 30 min debrief) where you'll build a REST API to manage candidates and their technical evaluations.

---

## Assessment Format

This assessment has **3 phases**:

### Phase 1: Briefing (15 minutes)
- Evaluator explains the project and answers your questions
- Fork the repository and set up your environment

### Phase 2: Execution (75 minutes) - RECORDING YOURSELF
- **You'll be ALONE** (evaluator not present)
- **Record your screen and audio** (Loom recommended)
- **Think out loud** - Explain your reasoning as you code
- Implement the 4 required features
- **STRICT TIME LIMIT: 75 minutes**

### Phase 3: Debrief (30 minutes)
- Evaluator will have reviewed your code and recording
- Discuss your implementation decisions and approach
- Technical Q&A

---

## What You'll Build

### Already Implemented

The foundation is ready:
- ✅ FastAPI application with automatic docs (Swagger UI)
- ✅ SQLAlchemy + SQLite database setup
- ✅ Health check endpoint (`GET /health`)
- ✅ Test infrastructure (pytest + in-memory SQLite)
- ✅ Docker setup (one command to run)
- ✅ Project structure with placeholder packages

### Your Tasks - 4 Required Features

You **MUST** implement these features (see **REQUIREMENTS.md** for full specs):

#### 1. Candidate CRUD
- Create, read, update candidates with status management
- Fields: email (unique), first_name, last_name, status
- Proper error handling (409 for duplicates, 404 for not found)

#### 2. Evaluations
- Record evaluation scores per category for each candidate
- Categories: functionality, code_quality, problem_solving, communication
- Score 1-5 per category, one evaluation per category per candidate

#### 3. Final Score Calculation
- Calculate weighted final score and hiring decision
- Formula: `(functionality × 0.40) + (code_quality × 0.25) + (problem_solving × 0.20) + (communication × 0.15)`
- Decision: hire (≥4.0), needs_calibration (≥3.0), no_hire (<3.0)

#### 4. Filtered Listing with Pagination
- Filter candidates by status, score range
- Sort by created_at, final_score, or last_name
- Paginated response with total count

---

## Rules

1. **Commit each feature separately** with descriptive messages
2. **Think out loud** while working (your screen is being recorded)
3. **AI tools are allowed** - but you must be able to explain every line of your code
4. **Work inside `app/`** - the project structure is already set up for you
5. **Tests are optional but valued** - the test infrastructure is ready in `tests/`
6. **Don't change the infrastructure** - no need to modify `database.py`, `config.py`, or `conftest.py`. You **will** need to modify `main.py` to register your routers and models (see the comments there).

---

## Getting Started

### Setup (During Briefing Phase)

1. **Fork this repository**

2. **Clone your fork**:
```bash
git clone https://github.com/YOUR-USERNAME/candidate-evaluation-api.git
cd candidate-evaluation-api
```

3. **Create your working branch**:
```bash
git checkout -b feature/implementation
```

4. **Start the application**:
```bash
# Option A: Use the setup script (recommended)
./setup.sh

# Option B: Manual with Docker
cp .env.example .env
docker compose up --build

# Option C: Local Python (without Docker)
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

5. **Verify everything works**:
- Swagger UI: http://localhost:8000/docs
- `GET /health` returns `{"status": "ok"}`
- Tests pass: `pytest -v` (local) or `docker compose exec app pytest -v` (Docker)

### During Execution Phase (75 minutes)

**When evaluator says "START":**

1. **START YOUR RECORDING** (Loom, Zoom, or similar)
2. Say the current time out loud
3. Open `REQUIREMENTS.md` - this file contains the full feature specs
4. Begin implementing the 4 features in `app/models/`, `app/schemas/`, `app/routers/`
5. **Think out loud** constantly - explain what you're doing and why

**When time is up (75 minutes):**

1. **STOP CODING** immediately
2. Commit your work:
```bash
git add .
git commit -m "Complete assessment: [list features completed]"
git push origin feature/implementation
```
3. **STOP YOUR RECORDING**
4. Upload video (Loom/YouTube unlisted)
5. Create Pull Request in YOUR fork
6. Send evaluator:
   - PR link
   - Recording link

---

## Project Structure

```
app/
├── main.py              # ← FastAPI app (configured)
├── config.py            # Settings (configured)
├── database.py          # DB engine & session (configured)
├── models/
│   └── __init__.py      # ← Your SQLAlchemy models here
├── schemas/
│   └── __init__.py      # ← Your Pydantic schemas here
├── routers/
│   ├── __init__.py
│   └── health.py        # Example endpoint (reference)
└── services/
    └── __init__.py      # ← Your business logic here (optional)

tests/
├── conftest.py          # Test client & DB fixtures (configured)
└── test_health.py       # Example test (reference)
```

---

## Database Schema

The database uses SQLite (file-based, no external services needed). You'll need to create these models:

```
candidates (
  id          INTEGER PRIMARY KEY,
  email       TEXT UNIQUE NOT NULL,
  first_name  TEXT NOT NULL,
  last_name   TEXT NOT NULL,
  status      TEXT DEFAULT 'applied',    -- applied, interviewing, evaluated, hired, rejected
  created_at  DATETIME,
  updated_at  DATETIME
)

evaluations (
  id              INTEGER PRIMARY KEY,
  candidate_id    INTEGER REFERENCES candidates(id),
  category        TEXT NOT NULL,          -- functionality, code_quality, problem_solving, communication
  score           INTEGER NOT NULL,       -- 1-5
  evaluator_notes TEXT,
  evaluated_at    DATETIME
)
```

---

## Useful Commands

```bash
# Start the app (Docker)
docker compose up

# Rebuild and start
docker compose up --build

# Run tests
docker compose exec app pytest -v

# Shell into the container
docker compose exec app bash

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Fresh start (deletes database)
docker compose down && rm -f app.db && docker compose up --build
```

---

## Evaluation Criteria

You'll be evaluated on:

1. **Functionality** (40%) - Do the features work correctly?
2. **Code Quality** (25%) - Clean, organized, well-structured code?
3. **Problem Solving** (20%) - How do you approach and solve challenges?
4. **Communication** (15%) - Can you explain your thinking clearly?

**Important**: We care more about **HOW** you solve problems than getting everything perfect.

---

## Tips for Success

### Time Management
- Don't get stuck on one feature for too long
- Start with basic implementations first
- Test as you go
- Commit frequently

### Communication
- **Think out loud constantly** - "I'm going to...", "This should...", "The error is..."
- Explain your decisions: "I'm using a service layer because..."
- Narrate what you're debugging: "Let me check the response..."

### If You Get Stuck
- Read error messages carefully
- Check `app/routers/health.py` for an endpoint example
- Check `tests/test_health.py` for a test example
- The Swagger UI at `/docs` is your best friend for testing
- Google and AI assistants are allowed - just explain your usage

---

## Troubleshooting

### Docker won't start
```bash
docker compose down
docker compose up --build
```

### Port already in use
```bash
lsof -ti:8000 | xargs kill  # Mac/Linux
```

### Module not found errors
```bash
docker compose up --build
```

### Database issues
- Delete `app.db` and restart the server
- The SQLite database is created automatically on startup

### Tests fail after model changes
- The test DB is in-memory and recreated each run
- Check your model definitions and imports
- Make sure models are imported so `Base.metadata.create_all()` picks them up

---
