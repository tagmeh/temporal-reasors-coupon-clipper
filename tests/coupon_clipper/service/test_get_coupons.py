import unittest
from unittest.mock import patch, MagicMock

from app.exceptions import OfferError
from app.coupon_clipper.service import ReasorsService
from app.coupon_clipper.schemas import AccountSession, Coupon, CouponResponse


class TestReasorsServiceGetCoupons(unittest.TestCase):
    """
    Tests the ReasorsService get_coupons and get_redeemed_coupons methods.

    The is_clipped arg on get_coupons isn't relevant to the return object structure testing.
    Either the endpoint returns coupons or not, both cases are handled in a deterministic way.
    """

    def setUp(self):
        self.service = ReasorsService()
        self.account: Account = Account(
            token="1a2b3c4d5e6f7g8h9i10j11k12l", store_id="1234", store_card_number="123456789011121314151617181920"
        )

        # Minimized payload from Reasors API call.
        self.successful_response = {
            "total": 100,
            "total_value": "$1,000,000.00",
            "items": [{"id": "ICE_1234_123123"}, {"id": "ICE_1234_123124"}, {"id": "ICE_1234_123125"}],
            "card_number": "400001234567",
            "card_number_barcode": "400001234567",
        }
        self.no_coupons_response = {
            "total": 100,
            # If no coupons, "total_value" and "items" are simply not returned.
            "card_number": "400001234567",
            "card_number_barcode": "400001234567",
        }

    @patch("coupon_clipper.service.requests.get")
    def test_get_coupons_success(self, get_mock):
        """Classic successful call that returns coupons."""
        # Arrange
        # Mock requests.get
        response_mock = MagicMock()
        response_mock.ok = True
        response_mock.json.return_value = self.successful_response

        get_mock.return_value = response_mock

        # Act
        response: CouponResponse = self.service.get_coupons(account_session=self.account, is_clipped=False)

        # Assert
        self.assertIsInstance(response, CouponResponse)
        # Note the property name change for clarity "total" to "coupon_count"
        self.assertEqual(response.coupon_count, self.successful_response["total"])
        self.assertEqual(response.total_value, self.successful_response["total_value"])
        self.assertIsInstance(response.coupons[0], Coupon)
        self.assertEqual(response.coupons[0].id, self.successful_response["items"][0]["id"])

    @patch("coupon_clipper.service.requests.get")
    def test_get_coupons_bad_token(self, get_mock):
        """API call with a bad token. Returns a 400, no coupons."""
        # Arrange
        # Mock requests.get
        response_mock = MagicMock()
        # Return error based on actual response.
        response_mock.ok = False
        response_mock.status_code = 400
        response_mock.json.return_value = {"error_code": "sign_out_required", "error_message": "Please log in again."}

        get_mock.return_value = response_mock

        # Act/Assert
        with self.assertRaises(OfferError) as err:
            self.service.get_coupons(account_session=self.account, is_clipped=False)

        self.assertIn("sign_out_required", err.exception.message)

    @patch("coupon_clipper.service.requests.get")
    def test_get_coupons_no_coupons(self, get_mock):
        """Successful API call that returns no coupons."""
        # Arrange
        # Mock requests.get
        response_mock = MagicMock()
        response_mock.ok = True
        response_mock.json.return_value = self.no_coupons_response

        get_mock.return_value = response_mock

        # Act
        response: CouponResponse = self.service.get_coupons(account_session=self.account, is_clipped=False)

        # Assert
        self.assertIsInstance(response, CouponResponse)
        # Note the property name change for clarity "total" to "coupon_count"
        self.assertEqual(response.coupon_count, self.successful_response["total"])
        self.assertEqual(response.total_value, "$0")
        self.assertEqual(response.coupons, [])
