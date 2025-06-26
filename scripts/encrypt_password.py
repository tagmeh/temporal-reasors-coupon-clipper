import os

from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from dotenv import dotenv_values

from typing import Any

import logging

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def encrypt_password(config: dict[str, Any], input_password: str) -> str:

    DECRYPTION_MASTER_KEY: str = config["DECRYPTION_MASTER_KEY"]
    if not DECRYPTION_MASTER_KEY:
        raise ValueError("DECRYPTION_MASTER_KEY must be set in the .env file. Needs to be some password-like string.")

    PASSWORD_SALT_BASE64: str = config["PASSWORD_SALT_BASE64"]

    password = DECRYPTION_MASTER_KEY.encode()
    try:
        salt = base64.b64decode(PASSWORD_SALT_BASE64)
    except (ValueError, TypeError):
        log.info("Invalid PASSWORD_SALT_BASE64 in .env file. Must be a base64 encoded string. Generating a new salt.")
        salt = None

    if not salt:
        salt = os.urandom(32)
        log.info(
            f"Using auto-generated salt: {base64.b64encode(salt).decode()}"
            f" - Please save this in the .env file for PASSWORD_SALT_BASE64."
        )

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    f = Fernet(key)

    plaintext_password = input_password.strip().encode()
    encrypted = f.encrypt(plaintext_password)
    return encrypted.decode()


if __name__ == "__main__":
    config = dotenv_values(".env")
    input_password = input("Plaintext Password: ")
    result = encrypt_password(config=config, input_password=input_password)
    print(result)
