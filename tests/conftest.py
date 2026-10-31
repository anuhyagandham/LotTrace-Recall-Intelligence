"""
Pytest configuration and shared fixtures for LotTrace AI.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.generator.data_generator import DataGenerator
from api import create_app


@pytest.fixture(scope="session")
def test_db_engine():
    """Provides an in-memory SQLite engine for rapid isolated unit testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Provides a fresh transactional database session for each test function."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def flask_test_client():
    """Provides a Flask HTTP test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
