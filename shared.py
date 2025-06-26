from datetime import date
from typing import Any

from pydantic import BaseModel, model_validator, ConfigDict
from typing_extensions import Self

from exceptions import MissingAccountInfoError

REASORS_COUPON_CLIPPER_TASK_QUEUE_NAME = "REASORS_COUPON_CLIPPER_TASK_QUEUE"


class Creds(BaseModel):
    """
    Initial user/pass passed in payload.
    Password is encrypted. The password is decrypted immediately before use,
    and no object is updated with it's decrypted value.
    """
    username: str
    password: str

    @model_validator(mode='after')
    def check_required_inputs(self) -> Self:
        if not self.username or not self.password:
            raise ValueError("Username and password must be provided.")
        return self


class Account(BaseModel):
    """
    An account representation. Technically authenticated with the server, however, if the store_id and store_card_number
    are missing, then we don't have enough information to query or clip coupons.
    """
    token: str
    store_id: str
    store_card_number: str

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        errors = []

        if not self.store_id or self.store_id == 0:
            errors.append("- Missing preferred store on website. Please select a store in order to claim coupons.")

        if not self.store_card_number:
            errors.append(
                "- Missing loyalty card number in website account. "
                "Visit Reasors to sign up for the card and add the number to your online account."
            )

        if errors:
            raise MissingAccountInfoError('\n'.join(errors))
        return self


class CouponConfig(BaseModel):
    """
    A config object within the coupon that contains easier to work with values.
    The alternative is to use string manipulation on values like: "$0.50" instead of using price_off: float.
    """
    model_config = ConfigDict(extra='allow')  # Stores extra fields in self.__pydantic_extra__

    type: str  # price_off  Might reference the 'price_off' variable. Unsure of all options
    price_off: float  # 0.5  Half a US Dollar
    quantity_maximum: float  # 1.0
    quantity_minimum: int | None = None

    def model_post_init(self, context: Any, /) -> None:
        """
        The returned fields from the API do not always contain every field.
        This is to identify the extra fields without throwing an exception or ignoring them.
        """
        if self.__pydantic_extra__:
            # TODO: Change to a logging system that works with Temporal.
            print(
                f"Additional fields passed into {self.__class__.__name__} model. "
                f"Consider updating the model. Fields: {self.__pydantic_extra__}"
            )


class Coupon(BaseModel):
    """
    A single coupon. May not contain all fields. Not all fields are returned for every coupon.
    However, the only field we need to clip the coupon is "id".
    Other fields like "is_redeemed" and the date fields may be used to track savings.
    """
    model_config = ConfigDict(
        extra='allow',  # Stores extra fields in self.__pydantic_extra__
        # arbitrary_types_allowed=True
    )

    id: str  # 'ice_123_123123' Used in the url when "clipping" the coupon
    name: str  # 'Save $0.50'
    description: str  # 'Best Choice Superior Selections...'
    brand: str  # 'Best Choice Superior Ultra Excellence Mega Grand Selections'
    department_id: str  # 'grocery'
    department: str  # 'Grocery'
    start_date: date  # 'YYYY-MM-DD'
    finish_date: date  # 'YYYY-MM-DD'
    clip_start_date: date  # 'YYYY-MM-DD'
    clip_end_date: date  # 'YYYY-MM-DD'
    is_redeemed: bool
    is_clipped: bool
    is_clippable: bool
    offer_value: str  # '$0.50'
    # Optionals, only here for potential future use.
    config: CouponConfig | None = None
    popularity: int | None = None  # 999999
    is_personalized: bool | None = None
    is_featured: bool | None = None
    offer_disclaimer: str | None = None  # 'Void if altered, etc'
    cover_image_url: str | None = None
    tags: list[str] | None = None  # ['issuer_store']
    quantity_maximum: int | None = None
    product_ids: list[str] | None = None
    status_id: str | None = None  # '12345'
    size: str | None = None  # '11 oz'
    sale_price: str | None = None  # '$0.50 off'
    split_quantity: int | None = None  # 1
    products_are_sold_by_weight: bool | None = None

    def model_post_init(self, context: Any, /) -> None:
        """
        The returned fields from the API do not always contain every field.
        This is to identify the extra fields without throwing an exception or ignoring them.
        """
        if self.__pydantic_extra__:
            # TODO: Change to a logging system that works with Temporal.
            print(
                f"Additional fields passed into {self.__class__.__name__} model. "
                f"Consider updating the model. Fields: {self.__pydantic_extra__}"
            )


class CouponResponse(BaseModel):
    """ The response object from the /1/offers? endpoint. """
    total_value: str  # "$5.00"
    coupon_count: int
    coupons: list[Coupon]


class ClipPayload(BaseModel):
    """ Input/Payload object passed into the clip coupons activity and service method."""
    account: Account
    coupons: list[Coupon]
