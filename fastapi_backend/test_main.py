from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_session():
    response = client.post("/api/session")

    assert response.status_code == 200

    data = response.json()

    assert "session_id" in data
    assert "token" in data
    assert data["session_id"]
    assert data["token"]


def test_chat_requires_authorization():
    response = client.post(
        "/api/chat",
        json={
            "session_id": "test-session",
            "query": "What is PM Vishwakarma scheme?",
            "language": "en",
        },
    )

    assert response.status_code in (401, 403)


def test_history_requires_authorization():
    response = client.get("/api/history/test-session")

    assert response.status_code in (401, 403)