import asyncio
import traceback
from datetime import UTC

from dotenv import dotenv_values
from temporalio.client import Client, WorkflowFailureError, Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from temporalio.contrib.pydantic import pydantic_data_converter

from app.coupon_clipper.schemas import REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME

config = dotenv_values(".env")


async def main() -> None:
    url = f"{config['SERVER_URL']}:{config['SERVER_PORT']}"
    # Create client connected to server at the given address
    client: Client = await Client.connect(url, namespace=config["NAMESPACE"], data_converter=pydantic_data_converter)

    try:
        if cron_schedule := config.get('CRON_SCHEDULE'):
            await client.create_schedule(
                "clip-coupons-workflow",
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        "ClipCouponsWorkflow",
                        id="Reasors Coupon Clipper Parent",
                        task_queue=REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME,
                    ),
                    spec=ScheduleSpec(cron_expressions=[cron_schedule], time_zone_name=config.get('TIME_ZONE', UTC)),
                ),
            )
        else:
            await client.execute_workflow(
                "ClipCouponsWorkflow",
                id="Reasors Coupon Clipper Parent",
                task_queue=REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME
            )
    except WorkflowFailureError:
        print("Got expected exception: ", traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
