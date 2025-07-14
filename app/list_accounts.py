import logging

from app.database_utils.schemas import Account
from app.database_utils.service import init_db, get_session

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def list_rows() -> None:
    session = get_session()
    account = session.query(Account).all()

    if not account:
        print("No accounts found. Use add_account <username> <password> to add an account.")

    else:
        for row in account:
            print(f"Row: {row.id:<2} Username: {row.username}")


if __name__ == "__main__":
    init_db()
    list_rows()
