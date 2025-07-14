import base64
import logging
import os
import sys

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

from app.database_utils.schemas import Account
from app.database_utils.service import init_db, get_session

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def encrypt_password(input_password: str) -> str:
    DECRYPTION_MASTER_KEY: str = os.environ["DECRYPTION_MASTER_KEY"]
    if not DECRYPTION_MASTER_KEY:
        raise ValueError("DECRYPTION_MASTER_KEY must be set in the .env file. Needs to be some password-like string.")

    PASSWORD_SALT_BASE64: str = os.environ["PASSWORD_SALT_BASE64"]

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


def insert_into_database(username: str, password: str) -> int:
    session = get_session()
    account = Account(username=username, password=password)
    session.add(account)
    session.commit()
    return account.id


if __name__ == "__main__":
    username = sys.argv[1]
    password = sys.argv[2]

    init_db()
    load_dotenv()

    if not username or not password:
        print("Please enter your username and password. e.g. python -m app.database.add_account username password.")
        exit(1)

    result = encrypt_password(input_password=password)

    account_id: int = insert_into_database(username=username, password=result)
    print(f"Username and Password stored in the database. ID: {account_id}")
