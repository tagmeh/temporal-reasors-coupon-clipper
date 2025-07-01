import unittest
from unittest.mock import patch

from cryptography.fernet import InvalidToken

from app.exceptions import ConfigError
from app.services.reasors_service import ReasorsService


class TestReasorsServiceDecryptPassword(unittest.TestCase):
    """
    Tests the ReasorsService.decrypt_password method.

    Does not test if the password is correct, only that it can be successfully decrypted.
    """

    def setUp(self):
        self.config = {
            "DECRYPTION_MASTER_KEY": "CoolMasterKeyPassword",
            "PASSWORD_SALT_BASE64": "3iAnyqPkGBpsECHJ7wmgykyM1vNfszt6HVy9gzKKzHY=",
        }
        patcher = patch("coupon_clipper.reasors_service.dotenv_values", return_value=self.config)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.service = ReasorsService()

        self.test_password = "TestPassword!"
        self.encrypted_test_password = (
            "gAAAAABoXitz81ntsDFH4PCj1Oeg8qBhpQfq-Bl0GmVAVi38lA0B4TFjfXWVtucPZFPos9R1ZzS7PdCJUHTdSNdvP5mnq3zOGw=="
        )

    def test_decrypt_password_success(self):
        # Act
        decrypted_password = self.service.decrypt_password(self.encrypted_test_password)

        # Assert
        self.assertEqual(decrypted_password, self.test_password, decrypted_password)

    def test_decrypt_password_missing_config_props(self):
        # Arrange
        del self.service.config["DECRYPTION_MASTER_KEY"]

        # Act/Assert
        with self.assertRaises(ConfigError):
            self.service.decrypt_password(self.encrypted_test_password)

    def test_decrypt_password_missing_config_props_2(self):
        # Arrange
        del self.service.config["PASSWORD_SALT_BASE64"]

        # Act/Assert
        with self.assertRaises(ConfigError):
            self.service.decrypt_password(self.encrypted_test_password)

    def test_decrypt_password_non_encrypted_input(self):
        # Arrange
        not_encrypted_test_password = "<PASSWORD>"

        # Act/Assert
        with self.assertRaises(InvalidToken):
            self.service.decrypt_password(not_encrypted_test_password)
