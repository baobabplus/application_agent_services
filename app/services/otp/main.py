import json
import logging
import os
from datetime import datetime, timezone

import requests

from app.core import settings as main_settings
from app.core.odoo_config import settings as odoo_settings
from app.core.otp_config import settings
from app.schemas.auth import AuthSchema
from app.schemas.otp import OTPResponseSchema
from app.schemas.token import TokenSchema
from app.schemas.user import UserSchema
from app.services.odoo.service import OdooService
from app.utils.main import (
    create_access_token,
    create_refresh_token,
    generate_secret,
    generate_totp,
    validate_and_extract_country,
    validate_totp,
)


class OTP:
    def __init__(self, phone_number: str):
        extracted_data = validate_and_extract_country(phone_number)
        self.phone_number = extracted_data["formatted_number"]
        self.country = extracted_data["country"]
        self.odoo_service = OdooService()

    def can_generate_new_otp(self):
        otp_id = self.odoo_service.search_last_otp_by_phone(
            self.phone_number,
        )
        if otp_id:
            create_date = otp_id[0]["create_date"]
            create_date = datetime.strptime(create_date, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
            current_date = datetime.now(timezone.utc)
            time_diff = current_date - create_date
            if time_diff.seconds < settings.otp_interval:
                second_left = settings.otp_interval - time_diff.seconds
                raise ValueError(
                    {
                        "error": "otp_spam",
                        "error_description": f"Please wait for {second_left} seconds before generating a new OTP",
                    }
                )

    def _generate_secret(self):
        return generate_secret(settings.otp_secret, self.phone_number)

    def send_otp(self):
        employee_id = self.odoo_service.search_employee_by_phone(self.phone_number)
        if employee_id and employee_id[0]["can_use_application_agent"]:
            secret = self._generate_secret()
            otp = generate_totp(secret)
            self.can_generate_new_otp()
            employee_id = employee_id[0]["id"]
            self.odoo_service.model_sms_otp.create(
                {
                    "name": otp,
                    "phone_number": self.phone_number,
                    "res_id": employee_id,
                    "res_model": "hr.employee",
                }
            )
            is_prod = main_settings.service_env.upper() not in ["LOCAL", "PREPROD"]
            message = f"OTP Sent to {self.phone_number}"
            if is_prod:
                return OTPResponseSchema(message=message)
            else:
                return OTPResponseSchema(
                    message=message,
                    otp=otp,
                )
        else:
            raise ValueError(
                {
                    "error": "Employee not found",
                    "error_description": f"Employee with phone number {self.phone_number} not found",
                }
            )

    def verify_otp(self, otp) -> TokenSchema:
        secret = self._generate_secret()
        is_valid = validate_totp(secret, otp)
        if not is_valid:
            self.odoo_service.deactive_otp_by_phone(self.phone_number)
            raise ValueError(
                {
                    "error": "otp_expired",
                    "error_description": "The OTP provided is expired",
                }
            )
        rec_id = self.odoo_service.search_otp_existance(self.phone_number, otp)
        if not rec_id:
            raise ValueError(
                {
                    "error": "otp_invalid",
                    "error_description": "The OTP provided is invalid",
                }
            )
        elif rec_id and not rec_id[0]["active"]:
            raise ValueError(
                {
                    "error": "otp_expired",
                    "error_description": "The OTP is already used",
                }
            )
        self.odoo_service.deactive_otp_by_phone(self.phone_number)
        employee_id = rec_id[0]["res_id"]
        employee_details = self.odoo_service.search_employee_by_id(employee_id)
        employee_details.pop("id")
        employee_details["sub"] = employee_id
        access_token = create_access_token(employee_details)
        expire_in = odoo_settings.access_token_expire * 60
        picture_url = f"{odoo_settings.odoo_url}/web/image/hr.employee.public/{employee_id}/image_512/image.jpeg"
        refresh_token = create_refresh_token({"sub": employee_id})
        self.odoo_service.set_refresh_token(employee_id, refresh_token)
        return AuthSchema(
            user=UserSchema(
                sub=employee_id,
                name=employee_details["name"],
                phonenumber=employee_details["mobile_phone"],
                loyality_points=10,
                picture=picture_url,
            ),
            token=TokenSchema(
                expires_in=expire_in,
                access_token=access_token,
                token_type="Bearer",
                refresh_token=refresh_token,
            ),
        )

    def send_sms(self, otp, employee_id, otp_id):
        SMS_URL = os.getenv("SMS_URL")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": os.getenv("API_KEY_SMS_REQUEST"),
        }
        msg = f"Your OTP code for login is {otp}. It will expire in 10 minutes. Do not share it with anyone"
        message_input = {
            "msisdn": self.phone_number,
            "msg": msg,
            "priority": "high",
            "client_app": "mobile_app_otp",
            "sms_id": f"{employee_id}-{otp_id}",
            "sms_ref": f"{employee_id}-{otp_id}-ref",
            "callback": False,
            "test": False,
        }
        response = requests.post(
            SMS_URL, data=json.dumps(message_input), headers=headers
        )
        logging.info(f"Response: {response.text}")
        return response
