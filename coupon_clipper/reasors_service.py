import base64
import datetime
from dataclasses import dataclass

import requests
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import dotenv_values
from temporalio import activity

from coupon_clipper.exceptions import AuthenticationError, OfferError, ConfigError
from coupon_clipper.shared import Account, Creds, CouponResponse, Coupon


@dataclass
class ReasorsService:
    def __init__(self) -> None:
        """Initialize the service"""
        self.base_url: str = "https://api.freshop.ncrcloud.com"
        self.headers: dict[str, str] = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "origin": "https://reasors.com",
            "referer": "https://reasors.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.8",
            "priority": "u=1, i",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
        }
        self.config = dotenv_values("../.env")

    def decrypt_password(self, encrypted_password: str) -> str:
        encoded_encrypted_password = encrypted_password.encode()
        try:
            password = self.config["DECRYPTION_MASTER_KEY"].encode()
            salt = base64.b64decode(self.config["PASSWORD_SALT_BASE64"])
        except KeyError as err:
            raise ConfigError(f"Missing configuration value in .env file: {err}")

        # Derive the key
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(password))

        f = Fernet(key)
        try:
            password = f.decrypt(encoded_encrypted_password).decode()
        except InvalidToken as err:
            activity.logger.error(f"Passed in non-encrypted password. Error: {err}")
            raise
        return password

    def authenticate(self, creds: Creds) -> Account:
        url = f"{self.base_url}/2/users/me/sessions"

        payload = {
            "app_key": "reasors",
            "email": creds.username,
            "password": self.decrypt_password(creds.password),
            "new_session_on_login": True,
            "referrer": "https://reasors.com/my-account#!/login?next=%2Fmy-account",
            "utc": int(datetime.datetime.now(datetime.UTC).timestamp() * 1000),
        }

        response = requests.post(url=url, headers=self.headers, data=payload)
        if response.ok:
            print(f"Authenticated")  # {creds.username}
            output: dict[str, str] = response.json()
            return Account(
                token=output["token"],  # Always exists, not technically tied to authentication.
                store_id=output.get("store_id", ""),
                store_card_number=output.get("store_card_number", ""),
            )
        else:
            raise AuthenticationError(f"Authentication Error: {response.status_code} - {response.content}")

    def get_coupons(self, account: Account, is_clipped: bool) -> CouponResponse:
        """Queries for available, unclipped coupons."""
        url = (
            f"{self.base_url}/1/offers?"
            "app_key=reasors&"
            f"is_clippable=true&"
            f"is_clipped={is_clipped}&"
            "limit=0&"
            "offer_value_sort=desc&"
            "sort=offer_value&"
            f"store_id={account.store_id}&"
            f"token={account.token}"
        )

        response = requests.get(url, verify=False, headers=self.headers)
        if response.ok:
            response_json = response.json()
            return CouponResponse(
                coupon_count=response_json["total"],  # Always exists.
                # These properties may not exist if there are no coupons returned.
                total_value=response_json.get("total_value", "$0"),
                coupons=[Coupon(**item) for item in response_json.get("items", [])],
            )
        else:
            raise OfferError(f"Get Coupons API Error: {response.status_code} - {response.json()}")

    def get_redeemed_coupons(self, account: Account) -> CouponResponse:
        """Contains the is_redeemed param, which, if present in get_coupons(), may return incomplete results. """
        url = (
            f"{self.base_url}/1/offers?"
            f"app_key=reasors&"
            f"is_redeemed=true&"
            f"offer_value_sort=desc&"
            f"sort=offer_value&"
            f"store_id={account.store_id}&"
            f"token={account.token}"
        )
        response = requests.get(url, verify=False, headers=self.headers)
        if response.ok:
            response_json = response.json()
            return CouponResponse(
                coupon_count=response_json["total"],  # Always exists.
                # These properties may not exist if there are no coupons returned.
                total_value=response_json.get("total_value", "$0"),
                coupons=[Coupon(**item) for item in response_json.get("items", [])],
            )
        else:
            raise OfferError(f"Redeemed API Error: {response.status_code} - {response.content}")


    def clip_coupon(self, account: Account, coupon: Coupon) -> Coupon:
        """
        Attempts to clip a coupon.
        Clipping a clipped coupon does not fail.
        """
        payload = {
            "app_key": "reasors",
            "referrer": "https://reasors.com/digital-coupons",
            "store_id": str(account.store_id),
            "token": account.token,
            "utc": int(datetime.datetime.now(datetime.UTC).timestamp() * 1000),
        }

        print(f"Clipping {coupon.id}")

        url = f"{self.base_url}/1/offers/{coupon.id}/clip"
        response = requests.post(url, data=payload, headers=self.headers, verify=False)
        # The response payload is not useful to this project.

        if response.ok:
            print(  # TODO: Use Temporal's logging. Also, find out where these logs exist in the GUI.
                f"Clipped coupon {coupon.id}. "
                f"Value: {coupon.offer_value} for {coupon.brand}: {coupon.description}"
            )
            # Updating is_clipped here, but we could just re-query the coupons to get the same value.
            coupon.is_clipped = True
        else:
            activity.logger.warn(f"Failed to clip coupon '{coupon.id}': {response.status_code} - {response.content}")

        print(f"{coupon.id=}")
        # TODO: Review activity timeouts. Do we need a heartbeat or a len(coupons)*5 seconds for the timeout.
        # activity.heartbeat(str(coupon.id))  # TODO: heartbeat fails if coupon.id is an empty string. Not sure why yet.

        return coupon
