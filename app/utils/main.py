import base64
import hashlib
import re
from datetime import datetime, timedelta, timezone

import jwt
import phonenumbers
import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from phonenumbers import NumberParseException, geocoder

from app.core.odoo_config import settings as odoo_settings
from app.core.otp_config import settings as otp_settings

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_jwt(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, odoo_settings.odoo_jwt_secret, algorithms=[ALGORITHM]
        )

        employee_id = payload.get("sub")
        if employee_id is None:
            raise credentials_exception

        return {"employee_id": employee_id}
    except InvalidTokenError:
        raise credentials_exception


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=odoo_settings.odoo_jwt_expire
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, odoo_settings.odoo_jwt_secret, algorithm=ALGORITHM
    )
    return encoded_jwt


def validate_and_extract_country(phone_number: str) -> dict:
    try:
        if "+" not in phone_number:
            phone_number = f"+{phone_number}"
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError(f"Invalid phone number: {phone_number}")

        formatted_number = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )

        country = geocoder.region_code_for_number(parsed_number)

        return {"formatted_number": formatted_number, "country": country}
    except NumberParseException as e:
        raise ValueError(f"Invalid phone number: {phone_number}. Error: {e}")


def generate_totp(secret: str) -> str:
    interval = otp_settings.otp_interval
    totp = pyotp.TOTP(secret, interval=interval)
    return totp.now()


def validate_totp(secret: str, otp: str) -> bool:
    interval = otp_settings.otp_interval
    otp_valid_window = otp_settings.otp_valid_window
    totp = pyotp.TOTP(secret, interval=interval)
    return totp.verify(otp, valid_window=otp_valid_window)


def generate_secret(base_secret, phone_number):
    combined = f"{base_secret}:{phone_number}"
    hash_result = hashlib.sha256(combined.encode()).digest()
    secret = base64.b32encode(hash_result).decode("utf-8").rstrip("=")
    return secret


def validate_order(value: str, valid_colums: list) -> str:
    match = re.match(rf"^({'|'.join(valid_colums)}) (asc|desc)$", value, re.IGNORECASE)
    if not match:
        raise ValueError("Invalid order format. Use '<column> asc' or '<column> desc'.")
    return value


def get_column_order(additional_field: list = []):
    order_field = ["id", "create_date"]
    order_field += additional_field
    return order_field


def generate_slow_payer_description():
    try:
        columns = get_column_order()
        transformed_columnt = [f"`{column}`" for column in columns]
        return (
            "This endpoint retrieves a list of clients who are slow payers assigned to a specific "
            "responsible employee. The `order` parameter should be formatted as 'column asc' or "
            "'column desc'. Possible columns for ordering are: {}.".format(
                ", ".join(transformed_columnt)
            )
        )
    except Exception:
        return (
            "This endpoint retrieves a list of clients who are slow payers assigned to a specific "
            "responsible employee. An error occurred while fetching the available columns for ordering."
        )


def get_week_range(offset: int = 0):
    """
    Get the start (Monday) and end (Sunday) dates of a specific week relative to the current week.

    Args:
        offset (int): The number of weeks to offset from the current week.
                      0 = current week, -1 = previous week, 1 = next week, etc.

    Returns:
        tuple: A tuple containing the start (Monday) and end (Sunday) dates of
        the specified week in 'YYYY-MM-DD' format.
    """
    today = datetime.now()
    current_monday = today - timedelta(days=today.weekday())
    target_monday = current_monday + timedelta(weeks=offset)
    target_sunday = target_monday + timedelta(days=6)

    start_of_week_str = target_monday.date()
    end_of_week_str = target_sunday.date()

    return start_of_week_str, end_of_week_str
