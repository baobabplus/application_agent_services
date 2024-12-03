from app.core.odoo_config import settings
from app.schemas.employee import EmployeeSchema
from app.schemas.incentive_event import IncentiveEventRecord, IncentiveEventResponse
from app.schemas.payg_account import PaygAccountRecord, PaygAccountResponse
from app.schemas.prospect import ProspectRecord, ProspectResponse
from app.utils.main import validate_and_extract_country

from .client import OdooAPI
from .models import Models


class OdooService:
    def __init__(self) -> None:
        self.odoo_client = OdooAPI()
        self.model_hr_employee = Models(
            client=self.odoo_client, model_name="hr.employee"
        )
        self.model_payg_account = Models(
            client=self.odoo_client, model_name="payg.account"
        )
        self.model_sms_otp = Models(client=self.odoo_client, model_name="sms.otp")
        self.model_payg_prospect = Models(
            client=self.odoo_client, model_name="payg.prospect"
        )
        self.model_incentive_event = Models(
            client=self.odoo_client, model_name="incentive.event"
        )

    # hr_employee methods
    def search_employee_by_id(self, employee_id: int):
        fields = list(EmployeeSchema.model_fields.keys())
        employee_id = self.model_hr_employee.search(
            domain=[["id", "=", employee_id]], fields=fields
        )

        return employee_id

    def search_employee_by_phone(self, phone_number: int):
        phone_number = validate_and_extract_country(phone_number)["formatted_number"]
        fields = list(EmployeeSchema.model_fields.keys())
        employee_id = self.model_hr_employee.search(
            domain=[["mobile_phone", "=", phone_number]], fields=fields
        )
        if not employee_id:
            raise ValueError(
                {
                    "message": "Employee not found",
                    "details": f"Employee with phone number {phone_number} not found",
                }
            )
        return employee_id

    def search_slower_payer_employee(
        self, responsible_employee_id: int, offset: int, limit: int, order: str
    ):
        account_ids = self.search_account_by_segmentation_and_responsible(
            responsible_employee_id, offset, limit, order
        )
        return PaygAccountResponse(
            count=len(account_ids), models="payg.account", records=account_ids
        )

    # sms_otp methods
    def search_last_otp_by_phone(self, phone_number: int):
        domain = [["phone_number", "=", phone_number], ["active", "in", [True, False]]]
        otp_id = self.model_sms_otp.search(
            domain=domain,
            fields=["id", "create_date"],
            limit=1,
            order="create_date desc",
        )

        return otp_id

    def search_otp_existance(self, phonenumber: str, otp: str):
        domain = [
            ["name", "=", otp],
            ["phone_number", "=", phonenumber],
            ["active", "in", [True, False]],
        ]
        fields = ["id", "res_id", "active"]
        otp_id = self.model_sms_otp.search(
            domain=domain, fields=fields, limit=1, order="create_date desc"
        )

        return otp_id

    def deactive_otp_by_phone(self, phonenumber: str):
        domain = [["phone_number", "=", phonenumber], ["active", "=", True]]
        otp_ids = self.model_sms_otp.search(domain=domain, fields=["id"])
        for otp_id in otp_ids:
            self.model_sms_otp.write(otp_id["id"], {"active": False})

    # payg_account methods
    def search_account_by_segmentation_and_responsible(
        self, responsible_employee_id: int, offset: int, limit: int, order: str
    ):
        segmentations = settings.odoo_account_segmentation_slow_payer.split(",")
        segmentation_ids = [
            int(segmentation_id)
            for segmentation_id in segmentations
            if segmentation_id.isdigit()
        ]
        domain = [
            ["account_segmentation_id", "in", segmentation_ids],
            ["responsible_agent_employee_id", "=", responsible_employee_id],
        ]
        fields = list(PaygAccountRecord.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        return account_id

    # payg_prospect methods
    def search_prospect_by_responsible_employee(
        self, responsible_employee_id: int, offset: int, limit: int, order: str
    ):
        domain = [
            ["responsible_employee_id", "=", responsible_employee_id],
        ]
        fields = list(ProspectRecord.model_fields.keys())
        prospect_ids = self.model_payg_prospect.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )
        return ProspectResponse(
            count=len(prospect_ids), models="payg.prospect", records=prospect_ids
        )

    # incentive.event methods
    def search_bonus_by_employee(
        self, employee_id: int, offset: int, limit: int, order: str
    ):
        domain = [
            ["beneficiary_employee_id", "=", employee_id],
            ["event_status", "=", "validated"],
        ]
        fields = list(IncentiveEventRecord.model_fields.keys())
        record_ids = self.model_incentive_event.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )
        return IncentiveEventResponse(
            count=len(record_ids), models="incentive.event", records=record_ids
        )
