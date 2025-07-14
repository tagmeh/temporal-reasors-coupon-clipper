import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ParentClosePolicy

with workflow.unsafe.imports_passed_through():
    from app.coupon_clipper.activities import ReasorsActivities


@workflow.defn
class ClipCouponsWorkflow:
    @workflow.run
    async def run(self) -> str:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=10),
            non_retryable_error_types=["JSONDecodeError", "ConfigError"],
        )

        # Query the database_utils Account table and get only the account IDs.
        account_ids: list[int] = await workflow.execute_activity(
            ReasorsActivities.get_account_ids, start_to_close_timeout=timedelta(seconds=30), retry_policy=retry_policy
        )

        print(f"Parent - Found {len(account_ids)} accounts.")

        # Spins up a child workflow for each ID found in the database_utils table Account
        tasks = [
            workflow.start_child_workflow(
                "ClipCouponsChildWorkflow",
                account_id,
                id=f"Reasors Coupon Clipper for ID: {account_id}",
                parent_close_policy=ParentClosePolicy.ABANDON,
            )
            for account_id in account_ids
        ]

        if tasks:
            await asyncio.gather(*tasks)
            print(f"Parent - Submitted {len(tasks)} tasks.")

        return f"Finished parent workflow. Ran for {len(tasks)} accounts."
