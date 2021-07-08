from starlette.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user():
    response = client.post(
        "/user",
        json={"name": "foobar"}
        )
    assert response.status_code == 200
    assert response.json()["user"]["name"] == "foobar"

def test_create_expense_percentage_correct():
    response = client.post(
        "/balance/create_expense",
        json={
            "user_id": "1234",
            "share_type": 0,
            "share_division": {
                "5": 25,
                "6": 25,
                "7": 25
            },
            "amount": 500
        }
        )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_expense_percentage_wrong():
    response = client.post(
        "/balance/create_expense",
        json={
            "user_id": "1234",
            "share_type": 0,
            "share_division": {
                "5": 25,
                "6": 25,
                "7": 75
            },
            "amount": 500
        }
        )
    assert response.status_code == 400
    # assert response.json() == {"mesage": "incorrect"}

def test_create_settlement():
    response = client.post(
        "/balance/create_settlement",
        json={
            "payer": "1234",
            "payee": "4567",
            "amount":500
        }
        )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_balance():
    response = client.get("/balance")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
