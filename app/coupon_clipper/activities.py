from temporalio import activity

from app.coupon_clipper.schemas import AccountSession, CouponResponse, ClipPayload, Coupon
from app.coupon_clipper.service import ReasorsService
from app.database_utils.schemas import Account
from app.database_utils.service import get_session, init_db
from app.exceptions import AuthenticationError, OfferError


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
    async def auth(self, account_id: int) -> AccountSession:
        try:
            return self.reasors_service.authenticate(account_id=account_id)
        except AuthenticationError as err:
            activity.logger.exception(err, exc_info=True)
            raise
        except Exception as err:
            activity.logger.exception(f"{account_id}: - Unhandled Auth Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def get_available_coupons(self, account_session: AccountSession) -> CouponResponse:
        try:
            coupon_response: CouponResponse = self.reasors_service.get_coupons(
                account_session=account_session, is_clipped=False
            )
            # TODO: Replace section with logging.
            if coupon_response.coupon_count > 0:
                print(
                    f"{account_session.db_id}:{account_session.username:<30}: Found {coupon_response.coupon_count} coupons!")
            else:
                print(f"{account_session.db_id}:{account_session.username:<30}: No new coupons.")
            return coupon_response
        except OfferError as err:
            activity.logger.exception(err, exc_info=True)
            raise
        except Exception as err:
            activity.logger.exception(
                f"{account_session.db_id}:{account_session.username:<30}: Unhandled Coupon Exception: {err}",
                exc_info=True)
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
            activity.logger.exception(
                f"{clip_payload.account_session.db_id}:{clip_payload.account_session.username:<30}: Unhandled Coupon Exception: {err}",
                exc_info=True)
            raise
