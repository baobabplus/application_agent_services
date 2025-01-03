from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer

from app.schemas.error import ErrorResponse
from app.schemas.otp import OTPResponse
from app.schemas.token import LogoutResponse, TokenResponse
from app.services.odoo.service import OdooService
from app.services.otp.main import OTP
from app.utils.main import handle_exceptions, verify_refresh_token

router = APIRouter()
security = HTTPBearer()


@router.post(
    "/send",
    summary="Send OTP",
    description="""This endpoint allows users to request an OTP (One-Time Password) to be
    sent to their phone number.
    The OTP is typically used for authentication or verification purposes.""",
    responses={
        200: {
            "model": OTPResponse,
            "description": "OTP sent successfully. The response contains information about the OTP request.",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid phone number or request format.",
        },
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
def send_otp(
    phone_number: str = Query(
        ...,
        description="The phone number, including the country code (e.g., 234XXXXXXXXXX)",
    ),
):
    my_otp = OTP(phone_number)
    return my_otp.send_otp()


@router.post(
    "/verify",
    summary="Verify OTP",
    description="""This endpoint verifies the OTP that was previously sent to the user's phone number.
    If the OTP is correct, an access token is returned.""",
    responses={
        200: {
            "model": TokenResponse,
            "description": "OTP verified successfully. A token is returned.",
        },
        400: {"model": ErrorResponse, "description": "Invalid OTP or phone number."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
def verify_otp(
    phone_number: str = Query(
        ...,
        description="The phone number, including the country code (e.g., 234XXXXXXXXXX)",
    ),
    otp: str = Query(..., description="OTP to verify", max_length=6, min_length=6),
):
    my_otp = OTP(phone_number)
    return my_otp.verify_otp(otp)


@router.post(
    "/refresh",
    summary="Refresh Token",
    description="""Refreshes the access token using a valid refresh token.
    This helps maintain the user's session without re-authentication.""",
    responses={
        200: {
            "model": TokenResponse,
            "description": "Token refreshed successfully. A new access token is returned.",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid or expired refresh token.",
        },
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
def refresh_access_token(payload: dict = Depends(verify_refresh_token)):
    odoo_service = OdooService()
    return odoo_service.refresh_token(payload)


@router.post(
    "/logout",
    summary="Logout User",
    description="""Logs out the user by invalidating the refresh token.
    This endpoint effectively ends the user's session.""",
    responses={
        200: {"model": LogoutResponse, "description": "User logged out successfully."},
        400: {"model": ErrorResponse, "description": "Invalid or missing token."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
def logout(payload: dict = Depends(verify_refresh_token)):
    odoo_service = OdooService()
    odoo_service.logout(payload)
    return LogoutResponse(message="User logged out successfully.")


send_otp = handle_exceptions(send_otp)
verify_otp = handle_exceptions(verify_otp)
refresh_access_token = handle_exceptions(refresh_access_token)
logout = handle_exceptions(logout)
