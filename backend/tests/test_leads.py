import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from sqlalchemy.orm import Session

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    # Erstellt die Tabellen vor jedem Test und löscht sie danach
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_create_lead(db_session: Session):
    # Testet das Erstellen eines Leads mit optionalem primären Kontakt
    lead = {
        "name": "Test Company",
        "domain": "test.com",
        "status": "new",
        "primary_contact": {
            "first_name": "Max",
            "last_name": "Mustermann",
            "emails": [{"value": "max@test.com", "is_primary": True}]
        }
    }

    response = client.post("/leads", json=lead)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Test Company"
    assert data["domain"] == "test.com"
    assert data["status"] == "new"
    assert data["primary_contact"] is not None
    assert data["primary_contact"]["first_name"] == "Max"
    assert data["primary_contact"]["emails"][0]["value"] == "max@test.com"


def test_get_leads(db_session: Session):
    # Vorher erstellten Lead abrufen
    response = client.get("/leads")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
