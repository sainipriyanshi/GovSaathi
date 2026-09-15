from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_chat():
    response = client.post(
        "/api/chat",
        json={
            "session_id": "test-session",
            "query": "Tell me about scholarships",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == "test-session"
    assert data["query"] == "Tell me about scholarships"
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["detected_language"], str)
    assert "created_at" in data


def test_history():
    response = client.get("/api/history/test-session")

    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == "test-session"
    assert "messages" in data