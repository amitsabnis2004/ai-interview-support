from __future__ import annotations

import re

import pytest

from app import create_app
from app import services
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    services.ROOT_DIR = tmp_path
    services.DB_PATH = tmp_path / "test.db"
    services.QUESTION_BANK_PATH = tmp_path / "question_bank.json"

    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{services.DB_PATH.as_posix()}",
            "LLM_ENABLED": False,
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def extract_interview_id(location: str) -> int:
    match = re.search(r"/interviews/(\d+)/live", location)
    if not match:
        raise AssertionError("Unable to extract interview id from redirect")
    return int(match.group(1))
