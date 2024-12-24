import base64
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

import phonenumbers
import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from phonenumbers import NumberParseException, geocoder

from app.core.odoo_config import settings as odoo_settings
from app.core.otp_config import settings as otp_settings
from app.services.odoo.exceptions import (
    EmployeeNotFoundException,
    UnauthorizedEmployeeException,
)

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()


def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, odoo_settings.access_token_secret, algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
        exp = payload.get("exp")

        if exp and datetime.now(tz=timezone.utc).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")

        if user_id is None:
            raise credentials_exception
        return payload

    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise credentials_exception
    except Exception as e:
        logging.error(f"Exception: {e}")
        raise credentials_exception


def create_access_token(data: dict):
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=odoo_settings.access_token_expire
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, odoo_settings.access_token_secret, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(tz=timezone.utc) + timedelta(
        days=odoo_settings.refresh_token_expire
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, odoo_settings.refresh_token_secret, algorithm=ALGORITHM
    )


def verify_refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, odoo_settings.refresh_token_secret, algorithms=[ALGORITHM]
        )
        return {
            "payload": payload,
            "token": token,
        }
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise credentials_exception
    except Exception as e:
        logging.error(f"Exception: {e}")
        raise credentials_exception


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


def filter_latest_event_by_status(data):
    for item in data:
        item["start_date"] = datetime.strptime(item["start_date"], "%Y-%m-%d")
        item["end_date"] = datetime.strptime(item["end_date"], "%Y-%m-%d")

    latest_by_status = {}
    for item in data:
        status = item["status"]
        if (
            status not in latest_by_status
            or item["start_date"] > latest_by_status[status]["start_date"]
        ):
            latest_by_status[status] = item

    for item in latest_by_status.values():
        item["start_date"] = item["start_date"]
        item["end_date"] = item["end_date"]

    return latest_by_status


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return wrapper


def handle_exceptions_employee(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except UnauthorizedEmployeeException as e:
            raise HTTPException(status_code=403, detail=e.details)
        except EmployeeNotFoundException as e:
            raise HTTPException(status_code=404, detail=e.details)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return wrapper
