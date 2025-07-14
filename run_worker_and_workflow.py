import asyncio

from app.run_worker import main as worker
from app.run_workflow import main as workflow


async def main():
    # Run worker and workflow concurrently
    await asyncio.gather(worker(), workflow())


if __name__ == "__main__":
    asyncio.run(main())
