import asyncio
import logging
import os
import traceback
from datetime import UTC

from temporalio.client import (
    Client,
    WorkflowFailureError,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleAlreadyRunningError,
)
from temporalio.contrib.pydantic import pydantic_data_converter

log = logging.getLogger(__name__)


async def main() -> None:
    start_workflow = os.getenv("START_WORKFLOW", "false").lower() == "true"
    namespace = os.getenv("NAMESPACE", "default")
    queue_name = os.getenv("QUEUE_NAME")

    print(f"Workflow - Starting Workflow: {start_workflow}")
    print(f"Workflow - Namespace: {namespace}")
    print(f"Workflow - Queue Name: {queue_name}")

    if not start_workflow:
        return

    url = f"{os.environ['SERVER_IP_ADDR']}:{os.environ['SERVER_PORT']}"

    print(f"Workflow - Connecting to {url}")
    # Create client connected to server at the given address
    client: Client = await Client.connect(url, namespace=namespace, data_converter=pydantic_data_converter)

    try:
        print(f"Workflow - Starting workflow on queue: {queue_name}")
        if cron_schedule := os.getenv("CRON_SCHEDULE", None):
            print(f"Workflow - CRON_SCHEDULE: {cron_schedule}")
            await client.create_schedule(
                "clip-coupons-workflow",
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        "ClipCouponsWorkflow",
                        id="Reasors Coupon Clipper Parent",
                        task_queue=queue_name,
                    ),
                    spec=ScheduleSpec(cron_expressions=[cron_schedule], time_zone_name=os.getenv("TIME_ZONE", UTC)),
                ),
            )
        else:
            print(f"Workflow - Running workflow on demand.")
            await client.execute_workflow(
                "ClipCouponsWorkflow",
                id="Reasors Coupon Clipper Parent",
                task_queue=queue_name,
            )

    except WorkflowFailureError:
        log.exception("Workflow - Got expected exception: ", traceback.format_exc())

    except ScheduleAlreadyRunningError:
        log.warning(
            "Workflow - A Schedule is already built for this workflow. "
            "To run on demand, clear the cron_schedule env variable. "
            "To change the schedule, delete the schedule within the UI and restart the container/script."
        )


if __name__ == "__main__":
    asyncio.run(main())
