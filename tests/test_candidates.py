def create_candidate(client, **kwargs):
    """Helper to create a candidate with default values."""
    data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
    }
    data.update(kwargs)
    return client.post("/candidates", json=data)


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


class TestCreateCandidate:
    def test_create_candidate_success(self, client):
        response = create_candidate(client)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["status"] == "applied"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_candidate_duplicate_email(self, client):
        create_candidate(client, email="duplicate@example.com")
        response = create_candidate(client, email="duplicate@example.com")
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_candidate_invalid_email(self, client):
        response = create_candidate(client, email="invalid-email")
        assert response.status_code == 422

    def test_create_candidate_empty_first_name(self, client):
        response = create_candidate(client, first_name="")
        assert response.status_code == 422

    def test_create_candidate_empty_last_name(self, client):
        response = create_candidate(client, last_name="")
        assert response.status_code == 422

    def test_create_candidate_with_status(self, client):
        response = create_candidate(client, status="interviewing")
        assert response.status_code == 201
        assert response.json()["status"] == "interviewing"


class TestListCandidates:
    def test_list_candidates_empty(self, client):
        response = client.get("/candidates")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["total_pages"] == 0

    def test_list_candidates_with_data(self, client):
        create_candidate(client, email="user1@example.com")
        create_candidate(client, email="user2@example.com")

        response = client.get("/candidates")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_candidates_filter_by_status(self, client):
        create_candidate(client, email="applied@example.com", status="applied")
        create_candidate(client, email="hired@example.com", status="hired")

        response = client.get("/candidates?status=hired")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "hired"

    def test_list_candidates_filter_by_score(self, client):
        resp1 = create_candidate(client, email="high@example.com")
        candidate1_id = resp1.json()["id"]
        create_complete_evaluations(client, candidate1_id, [5, 5, 5, 5])

        resp2 = create_candidate(client, email="low@example.com")
        candidate2_id = resp2.json()["id"]
        create_complete_evaluations(client, candidate2_id, [2, 2, 2, 2])

        create_candidate(client, email="no_eval@example.com")

        response = client.get("/candidates?min_score=4")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "high@example.com"

        response = client.get("/candidates?max_score=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "low@example.com"

    def test_list_candidates_sort_by_last_name(self, client):
        create_candidate(client, email="z@example.com", last_name="Zebra")
        create_candidate(client, email="a@example.com", last_name="Apple")

        response = client.get("/candidates?sort_by=last_name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["last_name"] == "Apple"
        assert data["items"][1]["last_name"] == "Zebra"

    def test_list_candidates_sort_by_final_score(self, client):
        resp1 = create_candidate(client, email="high@example.com")
        create_complete_evaluations(client, resp1.json()["id"], [5, 5, 5, 5])

        resp2 = create_candidate(client, email="low@example.com")
        create_complete_evaluations(client, resp2.json()["id"], [2, 2, 2, 2])

        response = client.get("/candidates?sort_by=final_score&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["email"] == "high@example.com"
        assert data["items"][1]["email"] == "low@example.com"

    def test_list_candidates_pagination(self, client):
        for i in range(5):
            create_candidate(client, email=f"user{i}@example.com")

        response = client.get("/candidates?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total_pages"] == 3

        response = client.get("/candidates?page=3&per_page=2")
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_candidates_per_page_capped_at_100(self, client):
        create_candidate(client)

        response = client.get("/candidates?per_page=200")
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 100

    def test_list_candidates_page_exceeds_total(self, client):
        create_candidate(client)

        response = client.get("/candidates?page=999")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetCandidate:
    def test_get_candidate_success(self, client):
        create_resp = create_candidate(client)
        candidate_id = create_resp.json()["id"]

        response = client.get(f"/candidates/{candidate_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == candidate_id
        assert data["email"] == "test@example.com"

    def test_get_candidate_not_found(self, client):
        response = client.get("/candidates/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateCandidate:
    def test_update_candidate_success(self, client):
        create_resp = create_candidate(client)
        candidate_id = create_resp.json()["id"]

        response = client.put(
            f"/candidates/{candidate_id}",
            json={"first_name": "Jane", "status": "hired"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["status"] == "hired"
        assert data["last_name"] == "Doe"

    def test_update_candidate_not_found(self, client):
        response = client.put(
            "/candidates/99999",
            json={"first_name": "Jane"},
        )
        assert response.status_code == 404

    def test_update_candidate_duplicate_email(self, client):
        create_candidate(client, email="existing@example.com")
        create_resp = create_candidate(client, email="another@example.com")
        candidate_id = create_resp.json()["id"]

        response = client.put(
            f"/candidates/{candidate_id}",
            json={"email": "existing@example.com"},
        )
        assert response.status_code == 409

    def test_update_candidate_invalid_status(self, client):
        create_resp = create_candidate(client)
        candidate_id = create_resp.json()["id"]

        response = client.put(
            f"/candidates/{candidate_id}",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 422
