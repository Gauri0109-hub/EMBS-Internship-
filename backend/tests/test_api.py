import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    """Fixture providing a TestClient configured with lifespan startup/shutdown events."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def auth_headers(client):
    """Fixture providing headers with a valid JWT token for default admin user."""
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# HEALTH & AUTHENTICATION TESTS
# ==========================================

def test_health_check(client):
    """Tests the main API health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_invalid_login(client):
    """Tests that incorrect login attempts return 401 Unauthorized."""
    response = client.post("/api/v1/auth/login", data={"username": "wronguser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "detail" in response.json()

def test_successful_login(client):
    """Tests that valid login returns access and refresh tokens."""
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_unauthorized_access(client):
    """Tests that protected routes block requests without valid token."""
    response = client.get("/api/v1/medicines")
    assert response.status_code == 401


# ==========================================
# MEDICINES CRUD TESTS
# ==========================================

def test_list_medicines(client, auth_headers):
    """Tests listing cataloged medicines for authenticated users."""
    response = client.get("/api/v1/medicines", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_create_and_delete_medicine(client, auth_headers):
    """Tests registration, retrieval, update, and deletion of a formulation."""
    # 1. Create medicine
    payload = {
        "medicine_name": "Test Medicine 100mg",
        "bilingual_name": "टेस्ट मेडिसिन १००mg",
        "unit_price": 12.50,
        "is_critical": True,
        "min_required_stock": 15
    }
    response = client.post("/api/v1/medicines", json=payload, headers=auth_headers)
    assert response.status_code == 200
    created_med = response.json()
    assert created_med["medicine_name"] == "Test Medicine 100mg"
    assert created_med["is_critical"] is True
    med_id = created_med["medicine_id"]

    # 2. Update medicine
    update_payload = {
        "medicine_name": "Test Medicine 100mg Updated",
        "bilingual_name": "टेस्ट मेडिसिन १००mg",
        "unit_price": 15.00,
        "is_critical": False,
        "min_required_stock": 20
    }
    response = client.put(f"/api/v1/medicines/{med_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["medicine_name"] == "Test Medicine 100mg Updated"
    assert response.json()["unit_price"] == 15.00

    # 3. Delete medicine
    response = client.delete(f"/api/v1/medicines/{med_id}", headers=auth_headers)
    assert response.status_code == 204


# ==========================================
# INVENTORY TESTS
# ==========================================

def test_list_inventory(client, auth_headers):
    """Tests fetching inventory batches for authenticated users."""
    response = client.get("/api/v1/inventory", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_log_incoming_batch(client, auth_headers):
    """Tests creating a batch in inventory."""
    # Find a valid medicine ID first
    med_resp = client.get("/api/v1/medicines", headers=auth_headers)
    med_id = med_resp.json()[0]["medicine_id"]

    payload = {
        "medicine_id": med_id,
        "batch_number": "TEST-BATCH-999",
        "quantity_stocked": 150,
        "expiry_date": "2027-12-31"
    }
    response = client.post("/api/v1/inventory", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["batch_number"] == "TEST-BATCH-999"
    assert response.json()["quantity_stocked"] == 150
    inv_id = response.json()["inventory_id"]

    # Clean up the test batch
    client.delete(f"/api/v1/inventory/{inv_id}", headers=auth_headers)


# ==========================================
# DEMAND FORECASTING TESTS
# ==========================================

def test_get_medicine_forecast(client, auth_headers):
    """Tests demand forecast generation for a seeded medicine."""
    med_resp = client.get("/api/v1/medicines", headers=auth_headers)
    med_id = med_resp.json()[0]["medicine_id"]

    response = client.get(f"/api/v1/forecast/{med_id}?days_to_forecast=7", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "medicine_name" in data
    assert "best_model_name" in data
    assert "forecast" in data
    assert len(data["forecast"]) == 7
