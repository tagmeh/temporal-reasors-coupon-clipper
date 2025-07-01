from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.activities.reasors_activities import ReasorsActivities
    from app.models.schemas import CouponResponse, ClipPayload, Coupon, AccountSession


@workflow.defn
class ClipCouponsChildWorkflow:
    @workflow.run
    async def run(self, account_id: int) -> str:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=10),
            non_retryable_error_types=["AuthenticationError", "MissingAccountInfoError", "OfferError"],
        )

        # Use DB Account to authenticate and return an AccountSession object.
        account_session: AccountSession = await workflow.execute_activity(
            ReasorsActivities.auth, account_id, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy
        )

        # Query the clippable coupons using the AccountSession
        coupon_response: CouponResponse = await workflow.execute_activity(
            ReasorsActivities.get_available_coupons,
            account_session,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Update the database with any new coupons.
        await workflow.execute_activity(
            ReasorsActivities.update_db_coupons,
            coupon_response.coupons,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        # Clip the available coupons.
        clipped_coupons: list[Coupon] = []
        for coupon in coupon_response.coupons:  # Coupon

            # TODO: Test if an interrupted workflow will resume mid-array, if it does, this section can be removed.
            if coupon.is_clipped:
                continue

            clipped_coupon: Coupon = await workflow.execute_activity(
                ReasorsActivities.clip_coupon,
                ClipPayload(account_session=account_session, coupon=coupon),
                start_to_close_timeout=timedelta(seconds=30),
                heartbeat_timeout=timedelta(seconds=10),
                retry_policy=retry_policy,
            )

            clipped_coupons.append(clipped_coupon)

        print(f"Clipped {len(clipped_coupons)} coupon(s)!")

        # Query if user has redeemed any coupons
        # Pending IRL testing.

        # update RedeemedCoupon database for the user, for each coupon.

        return str(len(coupon_response.coupons))
