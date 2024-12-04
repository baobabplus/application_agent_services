from datetime import date
from functools import wraps
from typing import List, Optional

from app.core.odoo_config import settings
from app.schemas.employee import EmployeeSchema
from app.schemas.incentive_event import (
    EventType,
    IncentiveEventRecord,
    IncentiveEventResponse,
)
from app.schemas.payg_account import PaygAccountRecord, PaygAccountResponse
from app.schemas.prospect import ProspectRecord, ProspectResponse
from app.services.odoo.exceptions import UnauthorizedEmployeeException
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
    def check_can_use_application_agent(method):
        @wraps(method)
        def wrapper(self, employee_id: int, *args, **kwargs):
            fields = ["id", "can_use_application_agent"]
            employee = self.model_hr_employee.search(
                domain=[["id", "=", employee_id]], fields=fields, limit=1
            )
            if not employee or (
                employee and not employee[0]["can_use_application_agent"]
            ):
                raise UnauthorizedEmployeeException(
                    "Unauthorized employee",
                    f"Employee ({employee_id}) is not authorized to use the application agent",
                )
            return method(self, employee_id, *args, **kwargs)

        return wrapper

    @check_can_use_application_agent
    def search_employee_by_id(self, employee_id: int):
        fields = list(EmployeeSchema.model_fields.keys())
        employee_id = self.model_hr_employee.search(
            domain=[["id", "=", employee_id]], fields=fields, limit=1
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
        elif not employee_id and employee_id[0]["can_use_application_agent"]:
            raise UnauthorizedEmployeeException(
                {
                    "message": "Unauthorized employee",
                    "details": "Employee is not authorized to use the application agent",
                }
            )
        return employee_id

    @check_can_use_application_agent
    def search_slower_payer_employee(
        self, employee_id: int, offset: int, limit: int, order: str
    ):
        account_ids = self.search_account_by_segmentation_and_responsible(
            employee_id, offset, limit, order
        )
        return PaygAccountResponse(
            count=len(account_ids), models="payg.account", records=account_ids
        )

    # sms_otp methods
    def search_last_otp_by_phone(self, phone_number: str):
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
    @check_can_use_application_agent
    def search_account_by_segmentation_and_responsible(
        self, employee_id: int, offset: int, limit: int, order: str
    ):
        segmentations = settings.odoo_account_segmentation_slow_payer.split(",")
        segmentation_ids = [
            int(segmentation_id)
            for segmentation_id in segmentations
            if segmentation_id.isdigit()
        ]
        domain = [
            ["account_segmentation_id", "in", segmentation_ids],
            ["responsible_agent_employee_id", "=", employee_id],
        ]
        fields = list(PaygAccountRecord.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        return account_id

    # payg_prospect methods
    @check_can_use_application_agent
    def search_prospect_by_responsible_employee(
        self, employee_id: int, offset: int, limit: int, order: str
    ):
        domain = [
            ["responsible_employee_id", "=", employee_id],
        ]
        fields = list(ProspectRecord.model_fields.keys())
        prospect_ids = self.model_payg_prospect.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )
        return ProspectResponse(
            count=len(prospect_ids), models="payg.prospect", records=prospect_ids
        )

    # incentive.event methods
    @check_can_use_application_agent
    def search_bonus_by_employee(
        self,
        employee_id: int,
        offset: int,
        limit: int,
        order: str,
        event_date_start: Optional[date] = None,
        event_date_end: Optional[date] = None,
    ):
        # Constants
        MAPPING_EVENT_TYPE = {
            "50-PERCENT-PAID": "Payment",
            "75-PERCENT-PAID": "Payment",
            "ACTIVATION": "Sales",
            "BUDG OPE": "BUDG OP",
            "HC-END-SEG-A": "HC END",
            "HC-END-SEG-B": "HC END",
            "HC-END-SEG-C": "HC END",
            "HC-END-SEG-D": "HC END",
            "PAIEMENT EXCL DP": "Payment",
            "PAIEMENT MANUEL": "Payment",
            "REPO-EARLY": "Repossession",
            "REPO-LATE": "Repossession",
            "RESELL-AFTER-REPO": "Sales",
            "RPP": "RPP",
            "WRITE OFF": "WRITE OFF",
            "UPSELL": "Sales",
            "DIRECT-SALE": "Sales",
            "MANUAL_EVENT": "Regularisation",
        }
        event_typ = list(MAPPING_EVENT_TYPE)
        # Build domain filters
        domain = self._build_bonus_domain(
            employee_id, event_date_start, event_date_end, event_typ
        )

        # Fetch fields and records
        fields = list(IncentiveEventRecord.model_fields.keys())
        record_ids = self.model_incentive_event.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        # Enrich records
        enriched_records = self._enrich_records(record_ids, MAPPING_EVENT_TYPE)

        return IncentiveEventResponse(
            count=len(enriched_records),
            models="incentive.event",
            records=enriched_records,
        )

    def _build_bonus_domain(
        self,
        employee_id: int,
        event_date_start: Optional[date],
        event_date_end: Optional[date],
        event_type: List[str],
    ) -> List:
        """Build the domain for searching incentive events."""
        domain = [
            ["beneficiary_employee_id", "=", employee_id],
            ["event_status", "=", "validated"],
            ["event_type_id.code", "in", event_type],
        ]
        if event_date_start:
            domain.append(["event_date", ">=", event_date_start.strftime("%Y-%m-%d")])
        if event_date_end:
            domain.append(["event_date", "<=", event_date_end.strftime("%Y-%m-%d")])
        return domain

    def _enrich_records(
        self, record_ids: List[dict], mapping_event_type: dict
    ) -> List[dict]:
        """Enrich records with event type and account details."""
        enriched_records = []
        for record in record_ids:
            # Enrich event type
            if record.get("event_type_id"):
                record["event_type_id"] = EventType(
                    id=record["event_type_id"][0],
                    name=record["event_type_id"][1],
                    category=mapping_event_type.get(
                        record["event_type_id"][1], "Other"
                    ),
                )

            # Enrich account details
            if record.get("account_id"):
                account_id = self._find_account_id(record)
                record["account_id"] = PaygAccountRecord(**account_id[0])

            enriched_records.append(record)
        return enriched_records

    def _find_account_id(self, record: dict) -> List[dict]:
        """Find account details for a given record."""
        fields = list(PaygAccountRecord.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=[["id", "=", record["account_id"][0]]],
            fields=fields,
            limit=1,
        )
        return account_id
