import os

from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from dotenv import dotenv_values


config = dotenv_values(".env")

password = config["DECRYPTION_MASTER_KEY"].encode()
salt = base64.b64decode(config["PASSWORD_SALT_BASE64"])

if not salt:
    salt = os.urandom(32)
    print(
        f"Using auto-generated salt: {base64.b64encode(salt).decode()}"
        f" - Please save this in the .env file for PASSWORD_SALT_BASE64."
    )

kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
key = base64.urlsafe_b64encode(kdf.derive(password))
f = Fernet(key)

plaintext_password = input("Plaintext Password: ").strip().encode()
encrypted = f.encrypt(plaintext_password)
print(encrypted.decode())
