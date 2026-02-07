# Feature Requirements

## Feature 1: Candidate CRUD

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/candidates` | Create a new candidate |
| `GET` | `/candidates` | List all candidates |
| `GET` | `/candidates/{id}` | Get candidate by ID |
| `PUT` | `/candidates/{id}` | Update candidate |

### Candidate Model

| Field | Type | Rules |
|-------|------|-------|
| `id` | integer | Auto-generated primary key |
| `email` | string | Required, unique, valid email format |
| `first_name` | string | Required, non-empty |
| `last_name` | string | Required, non-empty |
| `status` | enum | One of: `applied`, `interviewing`, `evaluated`, `hired`, `rejected`. Default: `applied` |
| `created_at` | datetime | Auto-generated (UTC) |
| `updated_at` | datetime | Auto-updated on changes (UTC) |

### Expected Behavior

- `POST /candidates` with duplicate email → `409 Conflict`
- `GET /candidates/{id}` with non-existent ID → `404 Not Found`
- `PUT /candidates/{id}` with invalid status → `422 Validation Error`
- Successful creation → `201 Created`

---

## Feature 2: Evaluations

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/candidates/{id}/evaluations` | Add an evaluation score for a candidate |
| `GET` | `/candidates/{id}/evaluations` | Get all evaluations for a candidate |

### Evaluation Model

| Field | Type | Rules |
|-------|------|-------|
| `id` | integer | Auto-generated primary key |
| `candidate_id` | integer | Foreign key to Candidate |
| `category` | enum | One of: `functionality`, `code_quality`, `problem_solving`, `communication` |
| `score` | integer | Required, between 1 and 5 (inclusive) |
| `evaluator_notes` | string | Optional, free text |
| `evaluated_at` | datetime | Auto-generated (UTC) |

### Expected Behavior

- A candidate can only have **one evaluation per category** (e.g., one `functionality` score, one `code_quality` score, etc.)
- `POST` with duplicate category for same candidate → `409 Conflict`
- `POST` for non-existent candidate → `404 Not Found`
- `POST` with score outside 1-5 → `422 Validation Error`
- `POST` with invalid category → `422 Validation Error`

---

## Feature 3: Final Score Calculation

### Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/candidates/{id}/final-score` | Calculate and return the weighted final score |

### Scoring Formula

```
Final Score = (functionality × 0.40) + (code_quality × 0.25) + (problem_solving × 0.20) + (communication × 0.15)
```

### Expected Response

```json
{
  "candidate_id": 1,
  "candidate_name": "John Doe",
  "final_score": 3.85,
  "decision": "needs_calibration",
  "categories": {
    "functionality": { "score": 4, "weight": 0.40, "weighted": 1.60 },
    "code_quality": { "score": 4, "weight": 0.25, "weighted": 1.00 },
    "problem_solving": { "score": 4, "weight": 0.20, "weighted": 0.80 },
    "communication": { "score": 3, "weight": 0.15, "weighted": 0.45 }
  },
  "evaluated_categories": 4,
  "total_categories": 4
}
```

### Decision Logic

| Final Score | Decision |
|-------------|----------|
| >= 4.0 | `hire` |
| >= 3.0 and < 4.0 | `needs_calibration` |
| < 3.0 | `no_hire` |

### Expected Behavior

- If the candidate has **no evaluations** → `400 Bad Request` with message indicating no evaluations exist
- If the candidate has **partial evaluations** (e.g., only 2 of 4 categories) → Up to you: return error, or calculate partial score. Document your decision.
- Non-existent candidate → `404 Not Found`

---

## Feature 4: Filtered Listing with Pagination

### Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/candidates` | Enhanced version of Feature 1's listing, with filters and pagination |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by candidate status (e.g., `?status=evaluated`) |
| `min_score` | float | Filter candidates with final score >= value |
| `max_score` | float | Filter candidates with final score <= value |
| `sort_by` | string | Sort field: `created_at` (default), `final_score`, `last_name` |
| `sort_order` | string | `asc` or `desc` (default: `desc`) |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 20, max: 100) |

### Expected Response

```json
{
  "items": [
    {
      "id": 1,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "status": "evaluated",
      "final_score": 3.85,
      "created_at": "2026-02-01T10:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

### Expected Behavior

- No results for filter → return empty `items` array (not 404)
- `per_page` > 100 → cap at 100
- `page` exceeds total pages → return empty `items` array
- `min_score`/`max_score` filters only apply to candidates who have a complete evaluation (all 4 categories scored)
