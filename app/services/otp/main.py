from datetime import datetime, timezone

from app.core import settings as main_settings
from app.core.otp_config import settings
from app.schemas.otp import OTPResponse
from app.services.odoo.service import OdooService
from app.utils.main import (
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
                        "message": "Cannot generate new OTP",
                        "details": f"Please wait for {second_left} seconds before generating a new OTP",
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
                return OTPResponse(message=message, success=True, record_id=employee_id)
            else:
                return OTPResponse(
                    message=message,
                    success=True,
                    otp=otp,
                    record_id=employee_id,
                )
        else:
            raise ValueError(
                {
                    "message": "Employee not found",
                    "details": f"Employee with phone number {self.phone_number} not found",
                }
            )

    def verify_otp(self, otp):
        secret = self._generate_secret()
        is_valid = validate_totp(secret, otp)
        if not is_valid:
            self.odoo_service.deactive_otp_by_phone(self.phone_number)
            raise ValueError(
                {"message": "Invalid OTP", "details": "The OTP provided is expired"}
            )
        rec_id = self.odoo_service.search_otp_existance(self.phone_number, otp)
        if not rec_id:
            raise ValueError(
                {
                    "message": "Invalid OTP",
                    "details": "The OTP provided is invalid",
                }
            )
        elif rec_id and not rec_id[0]["active"]:
            raise ValueError(
                {"message": "Invalid OTP", "details": "The OTP is already used"}
            )
        self.odoo_service.deactive_otp_by_phone(self.phone_number)
        # access_token = create_access_token({"sub": rec_id[0]["res_id"]})
        return OTPResponse(
            otp=otp,
            message="OTP Verified",
            record_id=rec_id[0]["res_id"],
            success=True,
            # access_token=access_token
        )
