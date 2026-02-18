def create_candidate(client, **kwargs):
    """Helper to create a candidate with default values."""
    data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }
    data.update(kwargs)
    response = client.post("/candidates", json=data)
    return response.json()["id"]


def create_evaluation(client, candidate_id, category, score, notes=None):
    """Helper to create an evaluation for a candidate."""
    data = {"category": category, "score": score}
    if notes:
        data["evaluator_notes"] = notes
    return client.post(f"/candidates/{candidate_id}/evaluations", json=data)


def create_complete_evaluations(client, candidate_id, scores):
    """Helper to create all 4 evaluations for a candidate."""
    categories = ["functionality", "code_quality", "problem_solving", "communication"]
    for category, score in zip(categories, scores):
        create_evaluation(client, candidate_id, category, score)


class TestCreateEvaluation:
    def test_create_evaluation_success(self, client):
        candidate_id = create_candidate(client)

        response = create_evaluation(client, candidate_id, "functionality", 4)
        assert response.status_code == 201
        data = response.json()
        assert data["candidate_id"] == candidate_id
        assert data["category"] == "functionality"
        assert data["score"] == 4
        assert "id" in data
        assert "evaluated_at" in data

    def test_create_evaluation_with_notes(self, client):
        candidate_id = create_candidate(client)

        response = create_evaluation(
            client, candidate_id, "code_quality", 5, notes="Excellent code quality"
        )
        assert response.status_code == 201
        assert response.json()["evaluator_notes"] == "Excellent code quality"

    def test_create_evaluation_candidate_not_found(self, client):
        response = create_evaluation(client, 99999, "functionality", 4)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_evaluation_duplicate_category(self, client):
        candidate_id = create_candidate(client)

        create_evaluation(client, candidate_id, "functionality", 4)
        response = create_evaluation(client, candidate_id, "functionality", 5)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_evaluation_invalid_score_too_low(self, client):
        candidate_id = create_candidate(client)

        response = create_evaluation(client, candidate_id, "functionality", 0)
        assert response.status_code == 422

    def test_create_evaluation_invalid_score_too_high(self, client):
        candidate_id = create_candidate(client)

        response = create_evaluation(client, candidate_id, "functionality", 6)
        assert response.status_code == 422

    def test_create_evaluation_invalid_category(self, client):
        candidate_id = create_candidate(client)

        data = {"category": "invalid_category", "score": 4}
        response = client.post(f"/candidates/{candidate_id}/evaluations", json=data)
        assert response.status_code == 422


class TestListEvaluations:
    def test_list_evaluations_success(self, client):
        candidate_id = create_candidate(client)
        create_evaluation(client, candidate_id, "functionality", 4)
        create_evaluation(client, candidate_id, "code_quality", 5)

        response = client.get(f"/candidates/{candidate_id}/evaluations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        categories = [e["category"] for e in data]
        assert "functionality" in categories
        assert "code_quality" in categories

    def test_list_evaluations_candidate_not_found(self, client):
        response = client.get("/candidates/99999/evaluations")
        assert response.status_code == 404

    def test_list_evaluations_empty(self, client):
        candidate_id = create_candidate(client)

        response = client.get(f"/candidates/{candidate_id}/evaluations")
        assert response.status_code == 200
        assert response.json() == []


class TestFinalScore:
    def test_final_score_complete(self, client):
        candidate_id = create_candidate(client)
        create_complete_evaluations(client, candidate_id, [4, 4, 4, 3])

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == candidate_id
        assert data["candidate_name"] == "John Doe"
        assert data["final_score"] is not None
        assert data["partial_score"] is None
        assert data["decision"] is not None
        assert data["evaluated_categories"] == 4
        assert data["total_categories"] == 4
        assert "functionality" in data["categories"]
        assert "code_quality" in data["categories"]
        assert "problem_solving" in data["categories"]
        assert "communication" in data["categories"]

    def test_final_score_partial(self, client):
        candidate_id = create_candidate(client)
        create_evaluation(client, candidate_id, "functionality", 4)
        create_evaluation(client, candidate_id, "code_quality", 4)

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()
        assert data["final_score"] is None
        assert data["partial_score"] is not None
        assert data["decision"] is None
        assert data["evaluated_categories"] == 2
        assert data["total_categories"] == 4

    def test_final_score_no_evaluations(self, client):
        candidate_id = create_candidate(client)

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 400
        assert "no evaluations" in response.json()["detail"].lower()

    def test_final_score_candidate_not_found(self, client):
        response = client.get("/candidates/99999/final-score")
        assert response.status_code == 404

    def test_final_score_hire_decision(self, client):
        candidate_id = create_candidate(client)
        create_complete_evaluations(client, candidate_id, [5, 5, 5, 5])

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()
        assert data["final_score"] >= 4.0
        assert data["decision"] == "hire"

    def test_final_score_needs_calibration_decision(self, client):
        candidate_id = create_candidate(client)
        create_complete_evaluations(client, candidate_id, [3, 3, 4, 4])

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()
        assert 3.0 <= data["final_score"] < 4.0
        assert data["decision"] == "needs_calibration"

    def test_final_score_no_hire_decision(self, client):
        candidate_id = create_candidate(client)
        create_complete_evaluations(client, candidate_id, [1, 1, 1, 1])

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()
        assert data["final_score"] < 3.0
        assert data["decision"] == "no_hire"

    def test_final_score_weighted_calculation(self, client):
        candidate_id = create_candidate(client)
        create_complete_evaluations(client, candidate_id, [4, 4, 4, 4])

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()

        categories = data["categories"]
        assert categories["functionality"]["score"] == 4
        assert categories["functionality"]["weight"] == 0.40
        assert categories["functionality"]["weighted"] is not None

        assert categories["code_quality"]["score"] == 4
        assert categories["code_quality"]["weight"] == 0.25

        assert categories["problem_solving"]["score"] == 4
        assert categories["problem_solving"]["weight"] == 0.20

        assert categories["communication"]["score"] == 4
        assert categories["communication"]["weight"] == 0.15

    def test_final_score_categories_have_null_for_missing(self, client):
        candidate_id = create_candidate(client)
        create_evaluation(client, candidate_id, "functionality", 4)

        response = client.get(f"/candidates/{candidate_id}/final-score")
        assert response.status_code == 200
        data = response.json()

        assert data["categories"]["functionality"]["score"] == 4
        assert data["categories"]["functionality"]["weighted"] is not None

        assert data["categories"]["code_quality"]["score"] is None
        assert data["categories"]["code_quality"]["weighted"] is None
