import json

from temporalio import activity

from coupon_clipper.db_models import Account, DBCoupon
from database.database_service import get_session, init_db

from coupon_clipper.exceptions import AuthenticationError, OfferError
from coupon_clipper.reasors_service import ReasorsService
from coupon_clipper.shared import AccountSession, CouponResponse, ClipPayload, Coupon


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
    async def update_db_coupons(self, coupons: list[Coupon]) -> None:
        """
        Updates the database with the queried coupons.
        """
        try:
            with get_session() as session:
                for coupon in coupons:  # Coupon
                    # Attempt to get the coupon from the database.
                    db_coupon = session.query(DBCoupon).filter_by(coupon_id=coupon.id).first()
                    if not db_coupon:
                        db_coupon = DBCoupon(
                            coupon_id=coupon.id,
                            name=coupon.name,
                            description=coupon.description,
                            brand=coupon.brand,
                            price=coupon.base_price,
                            price_off=coupon.config.price_off,
                            start_date=coupon.start_date,
                            finish_date=coupon.finish_date,
                            clip_start_date=coupon.clip_start_date,
                            clip_end_date=coupon.clip_end_date,
                        )
                        session.add(db_coupon)
                        session.flush()

                session.commit()

        except Exception as err:
            activity.logger.exception(f"Unhandled Database Exception: {err}", exc_info=True)
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
