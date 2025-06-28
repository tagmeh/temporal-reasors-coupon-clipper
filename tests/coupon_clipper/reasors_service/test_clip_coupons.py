import unittest
from unittest.mock import patch, MagicMock

from coupon_clipper.reasors_service import ReasorsService
from coupon_clipper.shared import Coupon, Account


class TestReasorsServiceClipCoupons(unittest.TestCase):
    """
    Tests the ReasorsService clip_coupons method.
    """

    def setUp(self):
        self.service = ReasorsService()
        self.account: Account = Account(
            token="1a2b3c4d5e6f7g8h9i10j11k12l",
            store_id="1234",
            store_card_number="123456789011121314151617181920"
        )

        self.unclipped_coupon = Coupon(id="ICE_1234_123123", is_clipped=False)
        self.bad_coupon = Coupon(id="", is_clipped=False)

    @patch("coupon_clipper.reasors_service.requests.post")
    def test_clip_coupon_success(self, post_mock):
        # Arrange
        # Mock requests.get
        response_mock = MagicMock()
        response_mock.ok = True

        post_mock.return_value = response_mock

        # Act
        coupon: Coupon = self.service.clip_coupon(account=self.account, coupon=self.unclipped_coupon)

        # Assert
        self.assertEqual(coupon.is_clipped, True)

    @patch("coupon_clipper.reasors_service.requests.post")
    def test_clip_coupon_failure(self, post_mock):
        """
        The function doesn't distinguish between a bad token, store_id, utc value, or bad coupon.
        Since this function is called in a loop, we just return the coupon and check later if it was successfully clipped.
        """
        # Arrange
        # Mock requests.get
        response_mock = MagicMock()
        response_mock.ok = False
        response_mock.status_code = 404
        response_mock.content = b'NotFound'

        post_mock.return_value = response_mock

        # Act
        coupon: Coupon = self.service.clip_coupon(account=self.account, coupon=self.bad_coupon)

        # Assert
        self.assertEqual(coupon.is_clipped, False)
