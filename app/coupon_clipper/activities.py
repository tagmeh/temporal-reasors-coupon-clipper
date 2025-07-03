import json

from temporalio import activity

from app.database.schemas import Account
from app.database.service import get_session, init_db

from app.exceptions import AuthenticationError, OfferError
from app.coupon_clipper.service import ReasorsService
from app.coupon_clipper.schemas import AccountSession, CouponResponse, ClipPayload, Coupon


class ReasorsActivities:
    reasors_service = ReasorsService()

    @activity.defn
    async def get_account_ids(self) -> list[int]:
        try:
            init_db()
            session = get_session()
            accounts = session.query(Account).all()
            return [account.id for account in accounts]

        except Exception as err:
            activity.logger.exception(f"Unhandled get_account_ids Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def get_accounts_json(self) -> list[dict[str, str]]:
        """
        Simply reads the accounts.json file,
        returning the contents of the "accounts" top-level property of the file contents.
        """
        try:
            with open("coupon_clipper/accounts.json", "r") as f:
                return json.load(f)["accounts"]  # type: dict[str, str]

        except FileNotFoundError as err:
            activity.logger.exception(f"Missing 'accounts.json' file in project directory. Error: {err}")
            raise
        except json.JSONDecodeError as err:
            activity.logger.exception(
                f"Error decoding JSON from accounts.json. " f"Ensure it is valid JSON format. Error: {err}"
            )
            raise
        except KeyError as err:
            activity.logger.exception(
                f'Likely missing "accounts" top-level key in accounts.json. ' f"See accounts-example.json. Error: {err}"
            )
            raise
        # TODO: Should every activity have a generic catchall Exception?

    @activity.defn
    async def auth(self, account_id: int) -> AccountSession:
        try:
            return self.reasors_service.authenticate(account_id=account_id)
        except AuthenticationError as err:
            activity.logger.exception(err, exc_info=True)
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Auth Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def get_available_coupons(self, account_session: AccountSession) -> CouponResponse:
        try:
            coupon_response: CouponResponse = self.reasors_service.get_coupons(
                account_session=account_session, is_clipped=False
            )
            # TODO: Replace section with logging.
            if coupon_response.coupon_count > 0:
                print(f"Found {coupon_response.coupon_count} coupons!")
            else:
                print("No new coupons.")
            return coupon_response
        except OfferError as err:
            activity.logger.exception(err, exc_info=True)
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def clip_coupon(self, clip_payload: ClipPayload) -> Coupon:
        try:
            return self.reasors_service.clip_coupon(
                account_session=clip_payload.account_session, coupon=clip_payload.coupon
            )
        except OfferError:
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise
