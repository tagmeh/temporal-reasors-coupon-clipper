import unittest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from app.coupon_clipper.service import ReasorsService
from app.database.schemas import Base, Account  # Adjust import paths


class TestReasorsServiceAuthenticate(unittest.TestCase):
    def setUp(self):
        self.service = ReasorsService()
        # Create a new in-memory SQLite DB
        engine = create_engine("sqlite:///:memory:")
        self.session = scoped_session(sessionmaker(bind=engine))

        # Create tables
        Base.metadata.create_all(engine)

        self.session.add(Account(username="Fry@PlanetExpress.com", password="<PASSWORD>"))

    @patch("app.coupon_clipper.service.get_session", MagicMock(return_value=Session))
    def test_get_db_account_success(self, session_mock):
        # Arrange
        session_mock.return_value = self.session

        # Act
        account = self.service.get_db_account(account_id=1)

        # Assert
        self.assertEqual(account.username, "Fry@PlanetExpress.com")
