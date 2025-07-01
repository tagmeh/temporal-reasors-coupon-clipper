import asyncio

from dotenv import dotenv_values
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig
from temporalio.worker import Worker

from coupon_clipper.activities import ReasorsActivities
from coupon_clipper.shared import REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME
from coupon_clipper.workflows import ClipCouponsWorkflow, ClipCouponsChildWorkflow

config = dotenv_values(".env")


async def main() -> None:
    url = f"{config['SERVER_URL']}:{config['SERVER_PORT']}"

    # Enables Metrics gathering/showing/somethinging
    prometheus_runtime = Runtime(telemetry=TelemetryConfig(metrics=PrometheusConfig(bind_address="0.0.0.0:7280")))

    client: Client = await Client.connect(
        url, namespace=config["NAMESPACE"], data_converter=pydantic_data_converter, runtime=prometheus_runtime
    )
    # Run the worker
    activities = ReasorsActivities()
    worker: Worker = Worker(
        client,
        task_queue=REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME,
        workflows=[ClipCouponsChildWorkflow, ClipCouponsWorkflow],
        activities=[
            activities.get_account_ids,
            activities.auth,
            activities.get_available_coupons,
            activities.update_db_coupons,
            activities.clip_coupon,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
