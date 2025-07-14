import logging
import sys

from app.database_utils.schemas import Account
from app.database_utils.service import init_db, get_session

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def delete_row(inp: str) -> None:
    session = get_session()

    try:
        value = int(inp)
        account = session.query(Account).filter(Account.id == value).first()
    except ValueError:
        account = session.query(Account).filter(Account.username.lower() == inp.lower()).first()

    session.delete(account)
    session.commit()
    print(f"Deleted row {account.id} - {account.username}")


if __name__ == "__main__":
    inp = sys.argv[1]  # Username or Row ID
    init_db()

    if not inp:
        print("Please enter the username or row id to remove..")
        exit(1)

    delete_row(inp=inp)
