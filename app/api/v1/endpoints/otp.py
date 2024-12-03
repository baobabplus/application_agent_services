from fastapi import APIRouter, HTTPException, Query

from app.schemas.error import ErrorResponse
from app.schemas.otp import OTPResponse
from app.services.otp.main import OTP

router = APIRouter()


@router.post(
    "/send",
    responses={
        200: {"model": OTPResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Send OTP to phone number",
    description="""
This endpoint generates and sends a **Time-Based One-Time Password (TOTP)** to the specified phone number.

- TOTP is valid for intervals of 30 seconds.
- TOTP expires after 15 minutes.
- The same user can only request a new TOTP once every 1 minute.

**Note for Test Version**: The TOTP will be included in the response. In production, it will only be sent via SMS.
    """,
)
def send_otp(
    phone_number: str = Query(
        ...,
        description="The phone number, including the country code (e.g., 234XXXXXXXXXX)",
    ),
):
    try:
        my_otp = OTP(phone_number)
        return my_otp.send_otp()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/verify",
    summary="Verify OTP",
    description="""
This endpoint verifies a One-Time Password (OTP) provided by the user.

- The OTP is typically time-based (TOTP) and valid for a specific interval (e.g., 30 seconds).
- This endpoint checks if the OTP is correct for the given phone number.
- If the OTP is invalid, expired, or does not match the provided phone number, an appropriate error is returned.

""",
)
def verify_otp(
    phone_number: str = Query(
        ...,
        description="The phone number, including the country code (e.g., 234XXXXXXXXXX)",
    ),
    otp: str = Query(..., description="OTP to verify"),
):
    try:
        my_otp = OTP(phone_number)
        return my_otp.verify_otp(otp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
