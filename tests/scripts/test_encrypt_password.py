import unittest
from encrypt_password import encrypt_password
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class TestEncryptPassword(unittest.TestCase):

    def setUp(self):
        # Mock the environment variables for testing
        self.config = {
            "DECRYPTION_MASTER_KEY": "my_secret_key",
            "PASSWORD_SALT_BASE64": "QetQQIyByY9weenprNwu6mHSI04R+CatvZ+OLx3KKzw=",
        }
        self.input_password = "my_password"
        self.padded_password = "  this password has leading and trailing spaces  "

    def test_encrypt_password(self):
        """Tests the encryption of the password is proper and can be decrypted."""
        encrypted_password = encrypt_password(self.config, self.input_password)

        # Derive the key again for decryption
        password = self.config["DECRYPTION_MASTER_KEY"].encode()
        salt = base64.b64decode(self.config["PASSWORD_SALT_BASE64"])
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(password))
        f = Fernet(key)

        decrypted = f.decrypt(encrypted_password.encode()).decode()
        self.assertEqual(decrypted, self.input_password)

    def test_encrypt_password_missing_config_salt(self):
        """
        Script should still generate an encrypted password even if PASSWORD_SALT_BASE64 is not set.
        Also outputs the used salt to the console so it can be saved in the .env file.
        """
        self.config["PASSWORD_SALT_BASE64"] = ""

        with self.assertLogs(level="INFO") as log:
            encrypted_password = encrypt_password(self.config, self.input_password)

        self.assertIsInstance(encrypted_password, str)
        self.assertGreater(len(encrypted_password), 0)
        self.assertIn("Using auto-generated salt:", log.output[0])

    def test_encrypt_password_invalid_salt(self):
        """Tests that an invalid base64 salt raises an error and generates a new salt."""
        self.config["PASSWORD_SALT_BASE64"] = "invalid_base64"

        with self.assertLogs(level="INFO") as log:
            encrypted_password = encrypt_password(self.config, self.input_password)

        self.assertIsInstance(encrypted_password, str)
        self.assertGreater(len(encrypted_password), 0)
        self.assertIn("Invalid PASSWORD_SALT_BASE64 in .env file.", log.output[0])
        self.assertIn("Using auto-generated salt:", log.output[1])

    def test_encrypt_password_missing_master_key(self):
        """Tests that a missing DECRYPTION_MASTER_KEY raises a ValueError."""
        self.config["DECRYPTION_MASTER_KEY"] = ""

        with self.assertRaises(ValueError) as context:
            encrypt_password(self.config, self.input_password)

        self.assertEqual(
            str(context.exception),
            "DECRYPTION_MASTER_KEY must be set in the .env file. Needs to be some password-like string.",
        )

    def test_encrypt_password_with_padded_input(self):
        """Tests that the function can handle passwords with leading and trailing spaces."""
        encrypted_password = encrypt_password(self.config, self.padded_password)

        # Derive the key again for decryption
        password = self.config["DECRYPTION_MASTER_KEY"].encode()
        salt = base64.b64decode(self.config["PASSWORD_SALT_BASE64"])
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(password))
        f = Fernet(key)

        decrypted = f.decrypt(encrypted_password.encode()).decode()
        self.assertEqual(decrypted, self.padded_password.strip())
