import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from coupon_clipper.workflows import ClipCouponsWorkflow


class TemporalWorkflowTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Sets up the environment to test Temporal Workflows.
    """
    WORKFLOWS = []
    ACTIVITIES = []

    async def asyncSetUp(self):
        """
        Sets up the base environment required to test a Temporal Workflow.
        If you have to mock or patch anything in the asyncSetUp() method, first do `await super().asyncSetUp()`.
        """
        # Create a time-skipping test workflow environment.
        self.env = await WorkflowEnvironment.start_time_skipping()
        # "enter" into the env context manager.
        self.env_cm = self.env.__aenter__()

        # Create the worker
        self.worker = Worker(
            self.env.client,
            task_queue="test-task-queue",
            workflows=self.WORKFLOWS,
            activities=self.ACTIVITIES,
        )
        # "Enter" into the worker context manager
        self.worker_cm = self.worker.__aenter__()

        await self.env_cm
        await self.worker_cm

    async def asyncTearDown(self):
        # Manually close the context managers.
        await self.worker.__aexit__(None, None, None)
        await self.env.__aexit__(None, None, None)


mocked_get_accounts_json_output = [
    {"username": "Fry@planetexpress.com", "password": "encrypted_password"},
    {"username": "Leela@planetexpress.com", "password": "encrypted_password"}
]


@activity.defn(name="get_accounts_json")
async def mocked_get_accounts_json() -> list[dict[str, str]]:
    return mocked_get_accounts_json_output


class TestClipCouponsWorkflow(TemporalWorkflowTestCase):
    # These properties are used to instantiate the Worker
    WORKFLOWS = [ClipCouponsWorkflow]
    ACTIVITIES = [mocked_get_accounts_json]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        # This mock allows us to avoid spawning child Workflows while testing the parent.
        self.mock_start_child = AsyncMock()
        self.mock_start_child.return_value = asyncio.Future()
        # The parent workflow is set to abandon the child workflows. So we don't care what the return values are.
        self.mock_start_child.return_value.set_result(None)

        patcher = patch("temporalio.workflow.start_child_workflow", self.mock_start_child)
        self.start_child_patch = patcher.start()  # Begins redirecting/patching.
        self.addCleanup(patcher.stop)  # Adds cleanup, so after these tests run, the patch is removed.

    async def test_clip_coupons_workflow(self):
        """ Tests the ClipCouponsWorkflow with mocked activities. """

        result = await self.env.client.execute_workflow(
            workflow="ClipCouponsWorkflow",
            id="clip-coupons-workflow-id",
            task_queue=self.worker.task_queue,
        )

        # Asserts the Workflow output.
        self.assertEqual(result, f"Finished parent workflow. Ran for {len(mocked_get_accounts_json_output)} accounts.",
                         f"Actual: {result}")
        # Asserts the correct number of child workflows were created.
        self.assertEqual(self.mock_start_child.call_count, len(mocked_get_accounts_json_output),
                         "A child job is expected for each account returned from the get_accounts_json activity.")
