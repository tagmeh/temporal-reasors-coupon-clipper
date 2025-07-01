import unittest
from unittest.mock import patch, MagicMock

from app.exceptions import AuthenticationError
from app.services.reasors_service import ReasorsService


class TestReasorsServiceAuthenticate(unittest.TestCase):
    def setUp(self):
        self.service = ReasorsService()  # Skipped mocking dotenv_values since it's not required.
        self.creds = Creds(
            username="Fry@planetexpress.com",
            password="encrypted_password",
        )

        # Mock the ReasorsService.decrypt_password method for all tests.
        self.decrypted_password = "decrypted_password"
        patcher = patch(
            "coupon_clipper.reasors_service.ReasorsService.decrypt_password", return_value=self.decrypted_password
        )
        self.addCleanup(patcher.stop)
        self.decrypt_password_mock = patcher.start()

    @patch("coupon_clipper.reasors_service.requests.post")
    def test_authenticate_success(self, post_mock):
        # Arrange
        request_json_response = {
            "token": "123123123asdf123123sdfs",
            "store_id": "1234",
            "store_card_number": "1234123123123123123",
        }

        # Mock requests.post
        response_mock = MagicMock()
        response_mock.ok = True
        response_mock.json.return_value = request_json_response

        post_mock.return_value = response_mock

        # Act
        result: Account = self.service.authenticate(creds=self.creds)

        # Assert
        self.assertIsInstance(result, Account)
        self.assertEqual(result.token, request_json_response["token"])
        self.assertEqual(result.store_id, request_json_response["store_id"])
        self.assertEqual(result.store_card_number, request_json_response["store_card_number"])

        # Verify/Require that the decrypt_password method was used.
        self.decrypt_password_mock.assert_called_once_with(self.creds.password)

    @patch("coupon_clipper.reasors_service.requests.post")
    def test_authenticate_wrong_password(self, post_mock):
        # Arrange
        response_mock = MagicMock()
        response_mock.ok = False
        response_mock.status_code = 403
        response_mock.content = "Bad Password =C"

        post_mock.return_value = response_mock

        # Act/Assert
        with self.assertRaises(AuthenticationError):
            self.service.authenticate(creds=self.creds)

        # Verify/Require that the decrypt_password method was used.
        self.decrypt_password_mock.assert_called_once_with(self.creds.password)
