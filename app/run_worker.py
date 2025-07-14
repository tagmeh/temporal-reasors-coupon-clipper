import asyncio
import os
import sqlite3
import urllib.parse

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig
from temporalio.worker import Worker

from app import ClipCouponsWorkflow, ClipCouponsChildWorkflow
from app.coupon_clipper.activities import ReasorsActivities


print("Running as UID:", os.getuid())
print(f"sqlite3.sqlite_version = {sqlite3.sqlite_version}")


async def main() -> None:
    url = f"{os.environ['SERVER_IP_ADDR']}:{os.environ['SERVER_PORT']}"

    print("Worker - Setting up Prometheus Runtime.")
    # Enables Metrics gathering/showing/somethinging
    prometheus_runtime = Runtime(telemetry=TelemetryConfig(metrics=PrometheusConfig(bind_address="0.0.0.0:7280")))

    print(f"Worker - Connecting to server: {url}")
    client: Client = await Client.connect(
        url, namespace=os.environ["NAMESPACE"], data_converter=pydantic_data_converter, runtime=prometheus_runtime
    )

    # Run the worker
    activities = ReasorsActivities()

    queue_name = os.environ["QUEUE_NAME"]

    print(f"Worker - Configuring Worker for queue: {queue_name}.")
    worker: Worker = Worker(
        client,
        task_queue=queue_name,
        workflows=[ClipCouponsWorkflow, ClipCouponsChildWorkflow],
        activities=[
            activities.get_account_ids,
            activities.auth,
            activities.get_available_coupons,
            activities.clip_coupon,
        ],
    )

    print("Worker - Starting.")
    await worker.run()
    print("Worker - Started successfully.")


if __name__ == "__main__":
    asyncio.run(main())
