from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_get_activities_returns_roster_without_cache(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert activity_name in response.json()
    assert response.json()[activity_name]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant_to_refreshed_roster(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity(client):
    # Arrange
    activity_name = "Chess Club"
    participants = app_module.activities[activity_name]["participants"]
    app_module.activities[activity_name]["max_participants"] = len(participants)
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant_from_roster(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_rejects_missing_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_is_served(client):
    # Arrange
    static_index_path = "/static/index.html"

    # Act
    response = client.get(static_index_path)

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text