import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ParentClosePolicy

with workflow.unsafe.imports_passed_through():
    from coupon_clipper.activities import ReasorsActivities
    from coupon_clipper.shared import Creds, Account, CouponResponse, ClipPayload, Coupon


@workflow.defn
class ClipCouponsChildWorkflow:
    @workflow.run
    async def run(self, creds: Creds) -> str:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=10),
            non_retryable_error_types=["AuthenticationError", "MissingAccountInfoError", "OfferError"],
        )

        account: Account = await workflow.execute_activity(
            ReasorsActivities.auth, creds, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy
        )

        coupon_response: CouponResponse = await workflow.execute_activity(
            ReasorsActivities.get_available_coupons,
            account,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        print(f"Found {len(coupon_response.coupons)} coupons.")

        clipped_coupons: list[Coupon] = await workflow.execute_activity(
            ReasorsActivities.clip_coupons,
            ClipPayload(account=account, coupons=coupon_response.coupons),
            start_to_close_timeout=timedelta(seconds=30),
            heartbeat_timeout=timedelta(seconds=10),
            retry_policy=retry_policy,
        )

        print(f"Clipped {len(clipped_coupons)} coupon(s)!")

        return str(len(coupon_response.coupons))


@workflow.defn
class ClipCouponsWorkflow:
    @workflow.run
    async def run(self) -> str:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=10),
            non_retryable_error_types=["JSONDecodeError", "KeyError"],
        )

        accounts: list[dict[str, str]] = await workflow.execute_activity(
            ReasorsActivities.get_accounts_json, start_to_close_timeout=timedelta(seconds=5), retry_policy=retry_policy
        )

        tasks = [
            workflow.start_child_workflow(
                "ClipCouponsChildWorkflow",
                Creds(username=account["username"], password=account["password"]),
                id=f"Reasors Coupon Clipper Child: {account['username'].lower().split('@')[0]}",
                parent_close_policy=ParentClosePolicy.ABANDON,
            )
            for account in accounts
        ]

        await asyncio.gather(*tasks)

        return f"Finished parent workflow. Ran for {len(accounts)} accounts."
