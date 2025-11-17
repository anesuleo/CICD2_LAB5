import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # allows only one session with StaticPool to avoid 'no such table' error

from app.main import app, get_db
from app.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, poolclass=StaticPool)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        # hand the client to the test
        yield c
        # --- teardown happens when the 'with' block exits ---

def test_create_user(client):
    r = client.post("/api/users", json={"name":"Paul","email":"pl@atu.ie","age":25,"student_id":"S1234567"})
    assert r.status_code == 201

def test_update_user(client):
    r = client.post("/api/users", json={"name":"Alice","email":"alice@example.com","age":22,"student_id":"S1111111"})
    assert r.status_code == 201
    user_id = r.json()["id"]

    payload = {"name":"Jane","email":"jane@example.com","age":24,"student_id":"S1111111"}
    r2 = client.put(f"/api/users/{user_id}", json=payload)

    assert r2.status_code == 202
    data = r2.json()
    assert data["name"] == "Jane"
    assert data["email"] == "jane@example.com"
    assert data["age"] == 24

def test_patch_user(client):
    r = client.post("/api/users", json={"name":"Bob","email":"bob@example.com","age":22,"student_id":"S2222222"})
    assert r.status_code == 201
    user_id = r.json()["id"]

    r2 = client.patch(f"/api/users/{user_id}", json={"email":"bobNew@example.com"})

    assert r2.status_code == 202
    data = r2.json()
    assert data["name"] == "Bob"
    assert data["email"] == "bobNew@example.com"
    assert data["age"] == 22
    assert data["student_id"] == "S2222222"

def test_put_project(client):
    # Create a user first
    r_user = client.post("/api/users", json={"name": "Owner1", "email": "owner1@example.com", "age": 30, "student_id": "S1000001"})
    assert r_user.status_code == 201
    owner_id = r_user.json()["id"]

    # Create a project
    r_proj = client.post("/api/projects", json={"name": "CICD 2", "description": "Xmas project", "owner_id": owner_id})
    assert r_proj.status_code == 201
    project_id = r_proj.json()["id"]

    # Full update with PUT
    payload = {"name": "Full Stack", "description": "React project", "owner_id": owner_id}
    r2 = client.put(f"/api/projects/{project_id}", json=payload)

    assert r2.status_code == 202
    data = r2.json()
    assert data["name"] == "Full Stack"
    assert data["description"] == "React project"
    assert data["owner_id"] == owner_id


def test_patch_project(client):
    # Create a user first
    r_user = client.post("/api/users", json={"name": "Owner2", "email": "owner2@example.com", "age": 28, "student_id": "S1000002"})
    assert r_user.status_code == 201
    owner_id = r_user.json()["id"]

    # Create a project
    r_proj = client.post("/api/projects", json={"name": "RTOS", "description": "RTOS mini project", "owner_id": owner_id})
    assert r_proj.status_code == 201
    project_id = r_proj.json()["id"]

    # Partial update with PATCH
    r2 = client.patch(f"/api/projects/{project_id}", json={"description":"Embedded RTOS project"})

    assert r2.status_code == 202
    data = r2.json()
    assert data["description"] == "Embedded RTOS project"
    assert data["name"] == "RTOS"
    assert data["owner_id"] == owner_id