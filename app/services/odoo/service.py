import logging
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
from app.schemas.incentive_report import IncentiveReport, IncentiveReportSimple
from app.schemas.payg_account import PaygAccountRecord, PaygAccountResponse
from app.schemas.token import TokenResponse
from app.services.odoo.exceptions import UnauthorizedEmployeeException
from app.utils.main import (
    create_access_token,
    create_refresh_token,
    filter_latest_event_by_status,
    validate_and_extract_country,
)

from .client import OdooAPI
from .models import Models


class OdooService:
    def __init__(self, user_context: dict = None) -> None:
        self.user_context = user_context or {}
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
        self.model_incentive_report = Models(
            client=self.odoo_client, model_name="incentive.report"
        )

    # hr_employee methods
    def check_can_use_application_agent(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user_context.get("can_use_application_agent", False):
                raise UnauthorizedEmployeeException(
                    "Unauthorized employee",
                    f"Employee ({self.user_context['sub']}) is not authorized to use the application agent",
                )
            return method(self, *args, **kwargs)

        return wrapper

    def search_employee_by_id(self, employee_id: int):
        fields = list(EmployeeSchema.model_fields.keys())
        employee_id = self.model_hr_employee.search(
            domain=[["id", "=", employee_id]], fields=fields, limit=1
        )
        logging.info(f"Employee: {employee_id}")
        return employee_id

    def search_employee_by_phone(self, phone_number: int):
        phone_number = validate_and_extract_country(phone_number)["formatted_number"]
        fields = ["id", "can_use_application_agent"]
        employee_id = self.model_hr_employee.search(
            domain=[["mobile_phone", "=", phone_number]], fields=fields
        )
        if not employee_id:
            raise ValueError(
                {
                    "error": "Employee not found",
                    "error_description": f"Employee with phone number {phone_number} not found",
                }
            )
        elif not employee_id and employee_id[0]["can_use_application_agent"]:
            raise UnauthorizedEmployeeException(
                {
                    "error": "Unauthorized employee",
                    "error_description": "Employee is not authorized to use the application agent",
                }
            )
        return employee_id

    @check_can_use_application_agent
    def get_slower_payer_client_service(
        self, employee_id: int, offset: int, limit: int, order: str
    ):
        account_ids = self.search_account_by_segmentation_and_responsible(
            employee_id, offset, limit, order
        )
        return PaygAccountResponse(
            count=len(account_ids), models="payg.account", records=account_ids
        )

    def set_refresh_token(self, employee_id: int, refresh_token: str):
        self.model_hr_employee.write(employee_id, {"refresh_token": refresh_token})

    def revoke_refresh_token(self, employee_id: int):
        self.model_hr_employee.write(employee_id, {"refresh_token": ""})

    def check_refresh_token(self, employee_id: int, token: str):
        employee_id = self.model_hr_employee.search(
            domain=[["id", "=", employee_id], ["refresh_token", "=", token]],
            fields=["id"],
            limit=1,
        )
        if not employee_id:
            raise ValueError(
                {
                    "error": "Invalid Refresh Token",
                    "error_description": "The refresh token provided is invalid",
                }
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
        self, offset: int, limit: int, order: str
    ):
        segmentations = settings.odoo_account_segmentation_slow_payer.split(",")
        segmentation_ids = [
            int(segmentation_id)
            for segmentation_id in segmentations
            if segmentation_id.isdigit()
        ]
        employee_id = int(self.user_context["sub"])
        domain = [
            ["account_segmentation_id", "in", segmentation_ids],
            ["responsible_agent_employee_id", "=", employee_id],
        ]
        fields = list(PaygAccountRecord.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        return account_id

    # incentive.report methods

    def search_latest_report_by_employee(self) -> dict:
        incentive_report_ids = self.search_incentive_report_by_employee()
        filtered_incentive_report_ids = filter_latest_event_by_status(
            incentive_report_ids
        )
        return filtered_incentive_report_ids

    def search_validate_report_by_employee(
        self,
    ) -> List[IncentiveReportSimple]:
        reports_ids = []
        incentive_report_ids = self.search_incentive_report_by_employee()
        for report in incentive_report_ids:
            if report["status"] == "done":
                reports_ids.append(
                    IncentiveReportSimple(
                        id=report["id"],
                        start_date=report["start_date"],
                        end_date=report["end_date"],
                        action=f"/api/v1/employee/report/{report['id']}/bonuses",
                    )
                )
        return reports_ids

    def search_incentive_report_by_employee(
        self,
    ) -> List[IncentiveReport]:
        fields = list(IncentiveReport.model_fields.keys())
        generic_job_id = self.user_context["generic_job_id"][0]
        company_id = self.user_context["company_id"][0]
        incentive_report_ids = self.model_incentive_report.search(
            [["generic_job_id", "=", generic_job_id], ["company_id", "=", company_id]],
            fields=fields,
        )
        return incentive_report_ids

    # incentive.event methods
    def search_bonuses_by_employee(self, period: str):
        status = "in_progress" if period == "current" else "done"
        latest_report_ids = self.search_latest_report_by_employee()
        current_report_id = latest_report_ids.get(status, False)
        if current_report_id:
            return self.search_bonuses(report_id=current_report_id["id"])
        return IncentiveEventResponse(
            count=0, models="incentive.event", total_value=0, records=[]
        )

    @check_can_use_application_agent
    def search_bonuses(
        self,
        offset: int = 0,
        limit: int = -1,
        order: str = "event_date desc",
        event_date_start: Optional[date] = None,
        event_date_end: Optional[date] = None,
        report_id: Optional[int] = None,
    ) -> IncentiveEventResponse:
        employee_valid_report = list(
            map(lambda item: item["id"], self.search_incentive_report_by_employee())
        )
        if report_id and report_id not in employee_valid_report:
            return IncentiveEventResponse(
                count=0, models="incentive.event", total_value=0, records=[]
            )
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
        employee_id = int(self.user_context["sub"])

        # Build domain filters
        domain = self._build_bonus_domain(
            employee_id, event_date_start, event_date_end, event_typ, report_id
        )

        # Fetch fields and records
        fields = list(IncentiveEventRecord.model_fields.keys())
        record_ids = self.model_incentive_event.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        # Enrich records
        enriched_records, total_value = self._enrich_records(
            record_ids, MAPPING_EVENT_TYPE
        )

        return IncentiveEventResponse(
            count=len(enriched_records),
            total_value=total_value,
            models="incentive.event",
            records=enriched_records,
        )

    def _build_bonus_domain(
        self,
        employee_id: int,
        event_date_start: Optional[date],
        event_date_end: Optional[date],
        event_type: List[str],
        report_id: Optional[int] = None,
    ) -> List:
        """Build the domain for searching incentive events."""
        domain = [
            ["beneficiary_employee_id", "=", employee_id],
            ["event_status", "in", ["validated", "calculated"]],
            ["event_type_id.code", "in", event_type],
        ]
        if report_id:
            domain.append(["report_id", "=", report_id])
        else:
            domain = [
                ["beneficiary_employee_id", "=", employee_id],
                ["event_status", "in", ["validated", "calculated"]],
                ["event_type_id.code", "in", event_type],
            ]
            if event_date_start:
                domain.append(
                    ["event_date", ">=", event_date_start.strftime("%Y-%m-%d")]
                )
            if event_date_end:
                domain.append(["event_date", "<=", event_date_end.strftime("%Y-%m-%d")])
        return domain

    def _enrich_records(
        self, record_ids: List[dict], mapping_event_type: dict
    ) -> List[dict]:
        """Enrich records with event type and account details."""
        enriched_records = []
        total_value = 0
        incentive_event_record = []
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
            total_value += record["value"]
            incentive_event_record.append(IncentiveEventRecord(**record))
        return enriched_records, total_value

    def _find_account_id(self, record: dict) -> List[dict]:
        """Find account details for a given record."""
        fields = list(PaygAccountRecord.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=[["id", "=", record["account_id"][0]]],
            fields=fields,
            limit=1,
        )
        return account_id

    def refresh_token(self, data: dict) -> TokenResponse:
        payload = data["payload"]
        logging.info(f"refresh_token Payload: {payload}")
        token = data["token"]
        employee_id = int(payload["sub"])
        self.check_refresh_token(employee_id, token)
        employee_details = self.search_employee_by_id(employee_id)[0]
        employee_details.pop("id")
        employee_details["sub"] = employee_id
        access_token = create_access_token(employee_details)
        expire_in = settings.access_token_expire * 60
        refresh_token = create_refresh_token({"sub": employee_id})
        self.set_refresh_token(employee_id, refresh_token)
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=expire_in,
            refresh_token=refresh_token,
        )

    def logout(self, data: dict) -> None:
        payload = data["payload"]
        token = data["token"]
        employee_id = int(payload["sub"])
        self.check_refresh_token(employee_id, token)
        self.revoke_refresh_token(employee_id)
