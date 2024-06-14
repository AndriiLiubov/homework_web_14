import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.database.models import Base
from src.database.db import get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope="module")
def user():
    return {"username": "deadpool", "email": "deadpool@example.com", "password": "123456789"}


@pytest.fixture(scope="module")
def contact():
    return {"first_name": "test_name", "last_name": "test_surname", "email": "test_email@test.com",
            "phone_number": "123456789", "birth_date": "2020-01-01", "additional_info": None}

@pytest.fixture(scope="module")
def new_contact():
    return {"first_name": "new_test_name", "new_last_name": "test_surname", "email": "new_test_email@test.com",
            "phone_number": "178456789", "birth_date": "2022-01-01", "additional_info": None}
