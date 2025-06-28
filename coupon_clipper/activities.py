import json

from temporalio import activity

from coupon_clipper.exceptions import AuthenticationError, OfferError
from coupon_clipper.reasors_service import ReasorsService
from coupon_clipper.shared import Creds, Account, CouponResponse, ClipPayload, Coupon


class ReasorsActivities:
    reasors_service = ReasorsService()

    @activity.defn
    async def get_accounts_json(self) -> list[dict[str, str]]:
        try:
            with open("accounts.json") as f:
                return json.load(f)["accounts"]  # type: dict[str, str]
        except json.JSONDecodeError:
            raise
        except KeyError as err:
            activity.logger.exception(
                f'Likely missing "accounts" top-level key in accounts.json. ' f"See accounts-example.json. Error: {err}"
            )
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled JSON Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def auth(self, creds: Creds) -> Account:
        try:
            return self.reasors_service.authenticate(creds=creds)
        except AuthenticationError:
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Auth Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def get_available_coupons(self, account: Account) -> CouponResponse:
        try:
            coupon_response: CouponResponse = self.reasors_service.get_coupons(account=account, is_clipped=False)
            if coupon_response.coupon_count > 0:
                print(f"Found {coupon_response.coupon_count} coupons!")
            else:
                print("No new coupons.")
            return coupon_response
        except OfferError:
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def clip_coupons(self, clip_payload: ClipPayload) -> list[Coupon]:
        try:
            output_coupons: list[Coupon] = []
            for coupon in clip_payload.coupons: # Coupon

                if coupon.is_clipped:
                    continue

                output_coupons.append(self.reasors_service.clip_coupon(account=clip_payload.account, coupon=coupon))

            return output_coupons
        except OfferError:
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise
