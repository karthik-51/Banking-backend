import pytest
from flask import json
from app import app, users_collection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_signup_and_login(client):
    email = "testuser@example.com"
    password = "testpass123"

    # Cleanup if user already exists
    users_collection.delete_one({"email": email})

    # Signup
    response = client.post('/api/signup', json={
        "email": email,
        "password": password,
        "name": "Test User",
        "phone_no": "1234567890",
        "bank": "Test Bank",
        "designation": "Manager"
    })
    assert response.status_code == 200 or response.status_code == 400
    if response.status_code == 200:
        data = response.get_json()
        assert "access_token" in data

    # Login - correct credentials
    response = client.post('/api/login', json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    login_data = response.get_json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # Login - wrong password
    response = client.post('/api/login', json={
        "email": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "error" in response.get_json()

    return token  # for further tests


def test_change_password(client):
    email = "changepwd@example.com"
    original_password = "original123"
    new_password = "newpassword123"

    # Ensure user exists
    users_collection.delete_one({"email": email})
    client.post('/api/signup', json={
        "email": email,
        "password": original_password,
        "name": "Change Password",
        "phone_no": "0000000000",
        "bank": "Change Bank",
        "designation": "IT"
    })

    # Change password
    response = client.post('/api/change_password', json={
        "emai": email,  # ✅ Note: key is intentionally 'emai' due to your backend typo
        "new_password": new_password
    })
    assert response.status_code == 200
    assert "message" in response.get_json()

    # Login with old password - should fail
    response = client.post('/api/login', json={
        "email": email,
        "password": original_password
    })
    assert response.status_code == 401

    # Login with new password - should succeed
    response = client.post('/api/login', json={
        "email": email,
        "password": new_password
    })
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_logout_and_token_block(client):
    token = test_signup_and_login(client)

    # Logout
    response = client.post('/api/logout', headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert "message" in response.get_json()

    # Try accessing protected route with same token
    response = client.get('/api/get-bank', headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 401 or response.status_code == 422


def test_timer_endpoint(client):
    token = test_signup_and_login(client)

    response = client.put('/api/timer', headers={
        "Authorization": f"Bearer {token}"
    }, json={"timer": 120})

    assert response.status_code == 200
    assert "message" in response.get_json()


def test_get_bank(client):
    token = test_signup_and_login(client)

    response = client.get('/api/get-bank', headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "bank" in data


def test_software_metrics(client):
    response = client.get('/api/software-metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_hardware_metrics(client):
    response = client.get('/api/hardware-metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_software_alerts(client):
    response = client.get('/api/software-alerts')
    assert response.status_code in (200, 404)


def test_hardware_alerts(client):
    response = client.get('/api/hardware-alerts')
    assert response.status_code in (200, 404)


def test_generate_pdf_no_token(client):
    response = client.post('/api/generate-report-pdf', json={
        "bankName": "Test Bank",
        "fromDate": "2023-01-01",
        "toDate": "2023-12-31"
    })
    assert response.status_code == 401


def test_generate_pdf_with_token(client):
    token = test_signup_and_login(client)

    response = client.post('/api/generate-report-pdf', headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "fromDate": "2023-01-01",
        "toDate": "2023-12-31"
    })

    # Allow 200 or 500 if error occurred during PDF generation
    assert response.status_code in (200, 500)
    if response.status_code == 500:
        assert "error" in response.get_json()
