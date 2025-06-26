import asyncio
import traceback

from temporalio.client import Client, WorkflowFailureError
from temporalio.contrib.pydantic import pydantic_data_converter

from shared import REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME
from workflows import ClipCouponsWorkflow


async def main() -> None:
    # Create client connected to server at the given address
    client: Client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)

    try:
        result = await client.execute_workflow(
            ClipCouponsWorkflow.run,
            id="Reasors Coupon Clipper Parent",
            task_queue=REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME,
        )

        print(f"Result: {result}")

    except WorkflowFailureError:
        print("Got expected exception: ", traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
