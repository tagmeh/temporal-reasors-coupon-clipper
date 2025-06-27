import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from coupon_clipper.workflows import ClipCouponsWorkflow

mocked_get_accounts_json_output = [
    {"username": "Fry@planetexpress.com", "password": "encrypted_password"},
    {"username": "Leela@planetexpress.com", "password": "encrypted_password"}
]


@activity.defn(name="get_accounts_json")
async def mocked_get_accounts_json() -> list[dict[str, str]]:
    return mocked_get_accounts_json_output


class TestClipCouponsWorkflow(unittest.TestCase):

    def test_clip_coupons_workflow(self):
        """ Tests the ClipCouponsWorkflow with mocked activities. """

        async def run_test():
            # Mock the start_child_workflow activity
            mock_start_child = AsyncMock()
            mock_start_child.return_value = asyncio.Future()
            # Since these child workflows are set to be abandoned, we don't need to set a .return_value.set_results()

            # Create a test environment that automatically skips any/all time delays.
            env = await WorkflowEnvironment.start_time_skipping()

            async with env:
                # Patch/Replace the start_child_workflow with the mock.
                with patch("temporalio.workflow.start_child_workflow", mock_start_child):
                    # Create the worker. Worker doesn't need to be able to run the child Workflow.
                    worker = Worker(
                        env.client,
                        task_queue="test-task-queue",
                        workflows=[ClipCouponsWorkflow],
                        activities=[mocked_get_accounts_json]
                    )

                    async with worker:

                        # Action (Test the Workflow)
                        result = await env.client.execute_workflow(
                            workflow="ClipCouponsWorkflow",
                            id="clip-coupons-workflow-id",
                            task_queue=worker.task_queue,
                        )

                        # Asserts the Workflow output.
                        self.assertEqual(
                            result,
                            f"Finished parent workflow. Ran for {len(mocked_get_accounts_json_output)} accounts.",
                            f"Actual: {result}")
                        # Asserts the correct number of child workflows were created.
                        self.assertEqual(
                            mock_start_child.call_count,
                            len(mocked_get_accounts_json_output),
                            "A child job is expected for each account returned from the get_accounts_json activity.")

        asyncio.run(run_test())
