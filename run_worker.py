import asyncio

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from coupon_clipper.activities import ReasorsActivities
from coupon_clipper.shared import REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME
from coupon_clipper.workflows import ClipCouponsWorkflow, ClipCouponsChildWorkflow


async def main() -> None:
    client: Client = await Client.connect("localhost:7233", namespace="default", data_converter=pydantic_data_converter)
    # Run the worker
    activities = ReasorsActivities()
    worker: Worker = Worker(
        client,
        task_queue=REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME,
        workflows=[ClipCouponsChildWorkflow, ClipCouponsWorkflow],
        activities=[
            activities.get_accounts_json,
            activities.auth,
            activities.get_available_coupons,
            activities.clip_coupons,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
