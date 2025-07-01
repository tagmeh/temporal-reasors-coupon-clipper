import json
import unittest
from unittest.mock import patch, mock_open

from temporalio.testing import ActivityEnvironment

from coupon_clipper.activities import ReasorsActivities
from coupon_clipper.exceptions import AuthenticationError, OfferError
from coupon_clipper.shared import Creds, Account, CouponResponse, Coupon


class TestReasorsActivities(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.activity_env = ActivityEnvironment()
        self.service = ReasorsActivities()
        self.creds = Creds(username="Fry@planetexpress.com", password="encrypted_password")
        self.account = Account(
            token="asd123aj1gds1df2f1s12s1f1", store_id="1077", store_card_number="121312577181273654"
        )
        self.coupon = Coupon(id="ICE_1234_123123")
        self.coupon_list = [self.coupon, Coupon(id="ICE_1234_1231234"), Coupon(id="ICE_1234_1231236")]

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
        """Test for an unhandled exception."""
        # Arrange
        authenticate_mock.side_effect = ArithmeticError("Unhandled Exception!")

        # Act/Assert
        with self.assertRaises(Exception):
            await self.activity_env.run(self.service.auth, self.creds)

        # TODO: Add assert for validating exception is logged at the activity level.

    @patch("coupon_clipper.activities.ReasorsService.get_coupons")
    async def test_get_available_coupons_success(self, get_coupons_mock):
        """Basic success test case. The underlying method is tested in more detail elsewhere."""
        # Arrange
        get_coupons_mock.return_value = CouponResponse(
            total_value="$1,000.00", coupon_count=len(self.coupon_list), coupons=self.coupon_list
        )

        # Act
        output: CouponResponse = await self.activity_env.run(self.service.get_available_coupons, self.account)

        # Assert
        self.assertIs(type(output), CouponResponse)
        self.assertEqual(len(output.coupons), len(self.coupon_list))

    @patch("coupon_clipper.activities.ReasorsService.get_coupons")
    async def test_get_available_coupons_success_no_coupons(self, get_coupons_mock):
        """Basic success test case. The underlying method is tested in more detail elsewhere."""
        # Arrange
        get_coupons_mock.return_value = CouponResponse(total_value="$0", coupon_count=0, coupons=[])

        # Act
        output: CouponResponse = await self.activity_env.run(self.service.get_available_coupons, self.account)

        # Assert
        self.assertIs(type(output), CouponResponse)
        self.assertEqual(len(output.coupons), 0)

    @patch("coupon_clipper.activities.ReasorsService.get_coupons")
    async def test_get_available_coupons_OfferError(self, get_coupons_mock):
        # Arrange
        get_coupons_mock.side_effect = OfferError("Get Coupons API Error: ")

        # Act/Assert
        with self.assertRaises(OfferError):
            await self.activity_env.run(self.service.get_available_coupons, self.account)

        # TODO: Add assert for validating exception is logged at the activity level"

    @patch("coupon_clipper.activities.ReasorsService.get_coupons")
    async def test_get_available_coupons_Exception(self, get_coupons_mock):
        """Test for an unhandled exception."""
        # Arrange
        get_coupons_mock.side_effect = ArithmeticError("Unhandled Exception!")

        # Act/Assert
        with self.assertRaises(Exception):
            await self.activity_env.run(self.service.get_available_coupons, self.account)

        # TODO: Add assert for validating exception is logged at the activity level.
