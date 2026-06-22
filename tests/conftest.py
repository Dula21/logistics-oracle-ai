import os

# CRITICAL: must be set before any app module is imported
os.environ["TESTING"] = "true"

from database import Base, engine
import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)