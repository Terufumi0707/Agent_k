from __future__ import annotations


def test_post_minutes_jobs_creates_job_from_transcript(api_client):
    response = api_client.post(
        "/minutes/jobs",
        json={"transcript": "定例会議の記録"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["status"] == "WAITING_FOR_REVIEW"
    assert len(body["candidates"]) > 0


def test_post_minutes_jobs_empty_transcript_returns_422(api_client):
    response = api_client.post(
        "/minutes/jobs",
        json={"transcript": "   "},
    )

    assert response.status_code == 422
    assert "transcript is required" in str(response.json()["detail"])


def test_get_minutes_jobs_not_found_returns_404(api_client):
    response = api_client.get("/minutes/jobs/not-found")

    assert response.status_code == 404


def test_review_api_approve_succeeds(api_client, started_job):
    response = api_client.post(
        f"/minutes/jobs/{started_job.id}/review",
        json={"selected_index": 0, "action": "approve"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["selected_candidate"] is not None


def test_review_api_revise_without_instruction_returns_400(api_client, started_job):
    response = api_client.post(
        f"/minutes/jobs/{started_job.id}/review",
        json={"selected_index": 0, "action": "revise"},
    )

    assert response.status_code == 400
    assert "instruction is required" in response.json()["detail"]


def test_review_api_invalid_selected_index_returns_error(api_client, started_job):
    response = api_client.post(
        f"/minutes/jobs/{started_job.id}/review",
        json={"selected_index": 999, "action": "approve"},
    )

    assert response.status_code == 400
    assert "selected_index is out of range" in response.json()["detail"]


def test_review_api_invalid_action_returns_validation_error(api_client, started_job):
    response = api_client.post(
        f"/minutes/jobs/{started_job.id}/review",
        json={"selected_index": 0, "action": "something_else"},
    )

    assert response.status_code == 422
