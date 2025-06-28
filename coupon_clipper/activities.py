import json

from temporalio import activity

from coupon_clipper.exceptions import AuthenticationError, OfferError
from coupon_clipper.reasors_service import ReasorsService
from coupon_clipper.shared import Creds, Account, CouponResponse, ClipPayload, Coupon


class ReasorsActivities:
    reasors_service = ReasorsService()

    @activity.defn
    async def get_accounts_json(self) -> list[dict[str, str]]:
        """
        Simply reads the accounts.json file,
        returning the contents of the "accounts" top-level property of the file contents.
        """
        try:
            with open("accounts.json", 'r') as f:
                return json.load(f)["accounts"]  # type: dict[str, str]
        except FileNotFoundError as err:
            activity.logger.exception(
                f"Missing 'accounts.json' file in project directory. Error: {err}"
            )
            raise
        except json.JSONDecodeError as err:
            activity.logger.exception(
                f"Error decoding JSON from accounts.json. "
                f"Ensure it is valid JSON format. Error: {err}"
            )
            raise
        except KeyError as err:
            activity.logger.exception(
                f'Likely missing "accounts" top-level key in accounts.json. '
                f'See accounts-example.json. Error: {err}'
            )
            raise
        # TODO: Should every activity have a generic catchall Exception?

    @activity.defn
    async def auth(self, creds: Creds) -> Account:
        try:
            return self.reasors_service.authenticate(creds=creds)
        except AuthenticationError as err:
            activity.logger.exception(err, exc_info=True)
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
        except OfferError as err:
            activity.logger.exception(err, exc_info=True)
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise

    @activity.defn
    async def clip_coupons(self, clip_payload: ClipPayload) -> list[Coupon]:
        try:
            output_coupons: list[Coupon] = []
            for coupon in clip_payload.coupons:  # Coupon

                if coupon.is_clipped:
                    continue

                output_coupons.append(self.reasors_service.clip_coupon(account=clip_payload.account, coupon=coupon))

            return output_coupons
        except OfferError:
            raise
        except Exception as err:
            activity.logger.exception(f"Unhandled Coupon Exception: {err}", exc_info=True)
            raise
