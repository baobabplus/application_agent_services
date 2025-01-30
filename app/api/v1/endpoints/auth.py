from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from app.schemas.auth import AuthSchema
from app.schemas.error import ErrorSchema
from app.schemas.otp import OTPResponseSchema
from app.schemas.token import LogoutSchema, TokenSchema
from app.services.odoo.service import OdooService
from app.services.otp.main import OTP
from app.utils.main import verify_refresh_token

router = APIRouter()
refresh_routeur = APIRouter()
user_router = APIRouter()
security = HTTPBearer()


@router.post(
    "/send",
    summary="Send OTP",
    description="""This endpoint allows users to request an OTP (One-Time Password) to be
    sent to their phone number.
    The OTP is typically used for authentication or verification purposes.""",
    responses={
        200: {
            "model": OTPResponseSchema,
            "description": "OTP sent successfully. The response contains information about the OTP request.",
        },
        400: {
            "model": ErrorSchema,
            "description": "otp_spam",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
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
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.post(
    "/verify",
    summary="Verify OTP",
    description="""This endpoint verifies the OTP that was previously sent to the user's phone number.
    If the OTP is correct, an access token is returned.""",
    responses={
        200: {
            "model": AuthSchema,
            "description": "OTP verified successfully. A token is returned.",
        },
        400: {
            "model": ErrorSchema,
            "description": "otp_expired, otp_invalid",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
def verify_otp(
    phone_number: str = Query(
        ...,
        description="The phone number, including the country code (e.g., 234XXXXXXXXXX)",
    ),
    otp: str = Query(..., description="OTP to verify", max_length=6, min_length=6),
):
    try:
        my_otp = OTP(phone_number)
        return my_otp.verify_otp(otp)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@refresh_routeur.post(
    "/refresh",
    summary="Refresh Token",
    description="""Refreshes the access token using a valid refresh token.
    This helps maintain the user's session without re-authentication.""",
    responses={
        200: {
            "model": TokenSchema,
            "description": "Token refreshed successfully. A new access token is returned.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid or expired refresh token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
def refresh_access_token(payload: dict = Depends(verify_refresh_token)):
    try:
        odoo_service = OdooService()
        return odoo_service.refresh_token(payload)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@user_router.post(
    "/logout",
    summary="Logout User",
    description="""Logs out the user by invalidating the refresh token.
    This endpoint effectively ends the user's session.""",
    responses={
        200: {"model": LogoutSchema, "description": "User logged out successfully."},
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
def logout(payload: dict = Depends(verify_refresh_token)):
    try:
        odoo_service = OdooService()
        odoo_service.logout(payload)
        return LogoutSchema(message="User logged out successfully.")
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)
