import json
import unittest
from unittest.mock import patch, mock_open

from temporalio.testing import ActivityEnvironment

from coupon_clipper.activities import ReasorsActivities
from coupon_clipper.exceptions import AuthenticationError
from coupon_clipper.shared import Creds, Account


class TestReasorsActivities(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.activity_env = ActivityEnvironment()
        self.service = ReasorsActivities()
        self.creds = Creds(username="Fry@planetexpress.com", password="encrypted_password")
        self.account = Account(
            token="asd123aj1gds1df2f1s12s1f1", store_id="1077", store_card_number="121312577181273654"
        )

    @patch("coupon_clipper.activities.open", new_callable=mock_open, read_data="[]")
    async def test_get_accounts_json_success(self, mock_file):
        # Arrange
        self.accounts_mock = {
            "accounts": [
                {"username": "Fry@planetexpress.com", "password": "encrypted_password"},
                {"username": "Leela@planetexpress.com", "password": "encrypted_password"},
            ]
        }
        self.file_content_mock = json.dumps(self.accounts_mock)
        mock_file.return_value.read.return_value = self.file_content_mock

        # Act
        output = await self.activity_env.run(self.service.get_accounts_json)

        # Assert
        self.assertEqual(len(output), 2, "There should be two accounts returned.")
        self.assertIsInstance(output, list)
        self.assertIsInstance(output[0], dict)
        self.assertIn("username", output[0])
        self.assertIn("password", output[0])

    @patch("coupon_clipper.activities.open", new_callable=mock_open, read_data="[]")
    async def test_get_accounts_json_JSONDecodeError(self, mock_file):
        # Arrange
        self.file_content_mock = '{"bad"; "json"}'
        mock_file.return_value.read.return_value = self.file_content_mock

        # Act/Assert
        with self.assertRaises(json.JSONDecodeError):
            await self.activity_env.run(self.service.get_accounts_json)

        # TODO: Add assert for validating exception is logged at the activity level.

    @patch("coupon_clipper.activities.open", new_callable=mock_open, read_data="[]")
    async def test_get_accounts_json_KeyError(self, mock_file):
        # Arrange
        self.file_content_mock = json.dumps(
            {"Incorrect": "accounts.json formatting. Missing top level 'account' property."}
        )
        mock_file.return_value.read.return_value = self.file_content_mock

        # Act/Assert
        with self.assertRaises(KeyError):
            await self.activity_env.run(self.service.get_accounts_json)

        # TODO: Add assert for validating exception is logged at the activity level.

    async def test_get_accounts_json_FileNotFoundError(self):
        # Arrange
        # Explicitly did not mock the file.

        # Act/Assert
        with self.assertRaises(FileNotFoundError):
            await self.activity_env.run(self.service.get_accounts_json)

        # TODO: Add assert for validating exception is logged at the activity level.

    @patch("coupon_clipper.activities.ReasorsService.authenticate")
    async def test_auth_success(self, authenticate_mock):
        """
        Simple auth call. This activity is very simple,
        only handling errors from calling ReasorsService.authenticate (which is tested more fully elsewhere).
        """
        # Arrange
        authenticate_mock.return_value = self.account

        # Act
        output: Account = await self.activity_env.run(self.service.auth, self.creds)

        # Assert
        self.assertIsInstance(output, Account)

    @patch("coupon_clipper.activities.ReasorsService.authenticate")
    async def test_auth_AuthenticationError(self, authenticate_mock):
        # Arrange
        authenticate_mock.side_effect = AuthenticationError("Authentication Error: 400 - response.content")

        # Act/Assert
        with self.assertRaises(AuthenticationError):
            await self.activity_env.run(self.service.auth, self.creds)

        # TODO: Add assert for validating exception is logged at the activity level.

    @patch("coupon_clipper.activities.ReasorsService.authenticate")
    async def test_auth_Exception(self, authenticate_mock):
        """ Test for an unhandled exception. """
        # Arrange
        authenticate_mock.side_effect = ArithmeticError("Unhandled Exception!")

        # Act/Assert
        with self.assertRaises(Exception):
            await self.activity_env.run(self.service.auth, self.creds)

        # TODO: Add assert for validating exception is logged at the activity level.