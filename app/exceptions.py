from dataclasses import dataclass

import urllib3

# Suppress only the single warning from urllib3.
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)


@dataclass
class AuthenticationError(Exception):
    """Exception for handling authentication issues.

    Attributes:
        message: The message to display.

    Args:
        message: The message to display.

    """

    def __init__(self, message) -> None:
        self.message: str = message
        super().__init__(self.message)


@dataclass
class MissingAccountInfoError(Exception):
    """Exception for handling when an account is missing a store_id (favorited store)
     or loyalty card associated to the account.

    Attributes:
        message: The message to display.

    Args:
        message: The message to display.

    """

    def __init__(self, message) -> None:
        self.message: str = message
        super().__init__(self.message)


@dataclass
class OfferError(Exception):
    """Exception for handling errors when querying offers (coupons).

    Attributes:
        message: The message to display.

    Args:
        message: The message to display.

    """

    def __init__(self, message) -> None:
        self.message: str = message
        super().__init__(self.message)


@dataclass
class ConfigError(Exception):
    """Exception for handling errors related to the .env file/dotenv config.

    Attributes:
        message: The message to display.

    Args:
        message: The message to display.

    """

    def __init__(self, message) -> None:
        self.message: str = message
        super().__init__(self.message)
