import logging
import random
from datetime import date, datetime, timedelta
from functools import wraps
from typing import List, Optional

from app.core.odoo_config import settings
from app.schemas.employee import EmployeeSchema
from app.schemas.global_schema import (
    CardSchema,
    CollapsedCardSchema,
    ExpandedSchema,
    FilterSchema,
    PaginationSchema,
    RowSchema,
    TaskCardSchema,
    TaskCollapsedCardSchema,
    TaskExpandedCardSchema,
    TaskSchema,
    TextTranslationSchema,
)
from app.schemas.incentive_event import (
    EventCategorySchema,
    EventTypeSchema,
    IncentiveEventSchema,
    IncentiveEventSummarySchema,
)
from app.schemas.incentive_report import (
    IncentiveReportDetailsSchema,
    IncentiveReportSchema,
    IncentiveReportSimpleSchema,
)
from app.schemas.payg_account import PaygAccountSchema
from app.schemas.screen import DateRangeSchema, SummarySimpleSchema, TasksSchema
from app.schemas.token import TokenSchema
from app.schemas.user import UserSchema
from app.services.odoo.exceptions import UnauthorizedEmployeeException
from app.utils.main import (
    create_access_token,
    create_refresh_token,
    filter_latest_event_by_status,
    get_filter,
    get_lang_from_company,
    validate_and_extract_country,
)

from .client import OdooAPI
from .models import Models

STATIC_COLOR_MAPPING = {
    "sales": "#F2BA11",
    "payment": "#AA54CC",
    "repossession": "#F26522",
    "penalty": "#39B54A",
    "hypercare": "#72cc1f",
}


class OdooService:
    def __init__(self, user_context: dict = None) -> None:
        self.user_context = user_context or {}
        self.lang = (
            get_lang_from_company(self.user_context["company_id"][0])
            if user_context
            else "en"
        )
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
        self.move_event_type = Models(client=self.odoo_client, model_name="event.type")

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
        return employee_id[0]

    def search_employee_by_phone(self, phone_number: int):
        phone_number = validate_and_extract_country(phone_number)["formatted_number"]
        fields = ["id", "can_use_application_agent", "company_id"]
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
        self,
        offset: int,
        limit: int,
        order: str = "nb_days_overdue asc",
        day_late: Optional[str] = None,
    ) -> TaskSchema:
        segmentations = settings.odoo_account_segmentation_slow_payer.split(",")
        segmentation_ids = [
            int(segmentation_id)
            for segmentation_id in segmentations
            if segmentation_id.isdigit()
        ]
        account_ids, total_count = self.search_account_by_segmentation_and_responsible(
            offset, limit, order, segmentation_ids=segmentation_ids
        )
        cards = []
        filter_day_late_new = get_filter("day_late", "new", self.lang)
        filter_day_late_urgent = get_filter("day_late", "urgent", self.lang)
        if day_late and day_late == "new":
            account_ids = list(
                filter(
                    lambda account_id: account_id["nb_days_overdue"] <= 15, account_ids
                )
            )
        elif day_late and day_late == "urgent":
            account_ids = list(
                filter(
                    lambda account_id: account_id["nb_days_overdue"] > 15, account_ids
                )
            )
        else:
            account_ids = account_ids
        for account_id in account_ids:
            filters = []
            if account_id["nb_days_overdue"] <= 15:
                filters.append(filter_day_late_new)
            elif account_id["nb_days_overdue"] > 15:
                filters.append(filter_day_late_urgent)
            sp_count = random.randint(1, 30)
            if sp_count < 10:
                alert_color = "#e0ce00"
            elif sp_count > 30 and sp_count < 60:
                alert_color = "#bf7404"
            elif sp_count > 60:
                alert_color = "#d12300"
            else:
                alert_color = "#000000"
            collapsed_item = TaskCollapsedCardSchema(
                icon="slow-payer-icon",
                icon_color="#F2BA11",
                title="Jane Doe",
                rows=[
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Nex commission", fr="Prochaine commission"
                        ),
                        value=TextTranslationSchema(en="500 Ar", fr="500 Ar"),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(en="Product", fr="Produit"),
                        value=TextTranslationSchema(
                            en="Solar Home System", fr="Solar Home System"
                        ),
                    ),
                ],
                alert_text=f"{account_id['nb_days_overdue']} days late in payment",
                alert_text_color=alert_color,
            )
            Expanded_item = TaskExpandedCardSchema(
                rows=[
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Client phone number", fr="Numéro de téléphone du client"
                        ),
                        value=TextTranslationSchema(
                            en="+261 32 68 510 46", fr="+261 32 68 510 46"
                        ),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Product name", fr="Nom du produit"
                        ),
                        value=TextTranslationSchema(
                            en="Solar Home System", fr="Solar Home System"
                        ),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Account age", fr="Age du compte"
                        ),
                        value=TextTranslationSchema(en="12 days", fr="12 jours"),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(en="Village", fr="Village"),
                        value=TextTranslationSchema(en="Ivato", fr="Ivato"),
                    ),
                ]
            )
            cards.append(
                TaskCardSchema(
                    filters=filters, collapsed=collapsed_item, expanded=Expanded_item
                )
            )
        return TaskSchema(
            icon="slow-payer-icon",
            title="Slow Payers",
            total_value=len(account_ids),
            pagination=PaginationSchema(
                offset=offset,
                limit=limit,
                current_records=len(account_ids),
                total_records=total_count,
            ),
            filters=[
                filter_day_late_new,
                filter_day_late_urgent,
            ],
            cards=cards,
        )

    def get_hypercare_at_risk_service(
        self, offset: int, limit: int, order: str = "registration_date desc"
    ) -> TaskSchema:
        segmentations = settings.odoo_account_segmentation_hypercare.split(",")
        segmentation_ids = [
            int(segmentation_id)
            for segmentation_id in segmentations
            if segmentation_id.isdigit()
        ]
        account_ids, total_count = self.search_account_by_segmentation_and_responsible(
            offset,
            limit,
            order,
            segmentation_ids=segmentation_ids,
            account_status="disabled",
        )

        filter_category_sav = get_filter("category", "sav", self.lang)
        filter_category_unreachable = get_filter("category", "unreachable", self.lang)

        cards = []
        for account_id in account_ids:
            registration_date = datetime.strptime(
                account_id["registration_date"], "%Y-%m-%d %H:%M:%S"
            )
            hypercare_end = registration_date + timedelta(days=75)
            hypercare_date_left = hypercare_end - datetime.now()
            if hypercare_date_left.days < 17:
                alert_color = "#bf7404"
            elif hypercare_date_left.days > 20:
                alert_color = "#d12300"
            else:
                alert_color = "#000000"
            filters = []
            cards.append(
                TaskCardSchema(
                    filters=filters,
                    collapsed=TaskCollapsedCardSchema(
                        icon="hypercare-icon",
                        icon_color="#F2BA11",
                        title=account_id["client_id"][1],
                        rows=[],
                        alert_text=f"{hypercare_date_left.days} days to hypercare end",
                        alert_text_color=alert_color,
                    ),
                    expanded=TaskExpandedCardSchema(
                        rows=[
                            RowSchema(
                                label=TextTranslationSchema(
                                    en="Client phone number",
                                    fr="Numéro de téléphone du client",
                                ),
                                value=TextTranslationSchema(
                                    en="+261 32 68 510 46", fr="+261 32 68 510 46"
                                ),
                            ),
                            RowSchema(
                                label=TextTranslationSchema(
                                    en="Product name", fr="Nom du produit"
                                ),
                                value=TextTranslationSchema(
                                    en="Solar Home System", fr="Solar Home System"
                                ),
                            ),
                            RowSchema(
                                label=TextTranslationSchema(en="Village", fr="Village"),
                                value=TextTranslationSchema(
                                    en="Ambohidratrimo", fr="Ambohidratrimo"
                                ),
                            ),
                        ],
                    ),
                )
            )

        return TaskSchema(
            icon="hypercare-icon",
            title="Hypercare at risk",
            total_value=len(account_ids),
            pagination=PaginationSchema(
                offset=offset,
                limit=limit,
                current_records=limit,
                total_records=total_count,
            ),
            filters=[filter_category_sav, filter_category_unreachable],
            cards=cards,
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

    def get_employee_profile(self):
        employee_id = self.search_employee_by_id(int(self.user_context["sub"]))
        emp_uid = employee_id["id"]
        picture_url = f"{settings.odoo_url}/web/image/hr.employee.public/{emp_uid}/image_512/image.jpeg"
        return UserSchema(
            sub=employee_id["id"],
            name=employee_id["name"],
            phonenumber=employee_id["mobile_phone"],
            loyality_points=10,
            job_title=employee_id["generic_job_id"][1],
            picture=picture_url,
        )

    def get_employee_tasks(self) -> List[TasksSchema]:
        return [
            TasksSchema(
                icon="units-repossess-icon",
                label="Units to Repossess",
                count=12,
                action="/api/v1/employee/unit-repossess",
                color="#F2BA11",
            ),
            TasksSchema(
                icon="to-do-icon",
                label="Actions to do",
                count=18,
                action="/api/v1/employee/todo",
                color="#AA54CC",
            ),
            TasksSchema(
                icon="slow-payer-icon",
                label="Slow Payer",
                count=30,
                action="/api/v1/employee/tasks/slower-payer",
                color="#F26522",
            ),
            TasksSchema(
                icon="hypercare-icon",
                label="Hypercare at Risk",
                count=0,
                action="/api/v1/employee/hypercare",
                color="#72cc1f",
            ),
        ]

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
        self,
        offset: int,
        limit: int,
        order: str,
        segmentation_ids: List[int],
        account_status: str = None,
    ):
        employee_id = int(self.user_context["sub"])
        domain = [
            ["account_segmentation_id", "in", segmentation_ids],
            ["responsible_agent_employee_id", "=", employee_id],
        ]
        if account_status:
            domain.append(["account_status", "=", account_status])
        fields = list(PaygAccountSchema.model_fields.keys())
        all_account_ids = self.model_payg_account.search(domain=domain, fields=["id"])
        account_ids = self.model_payg_account.search(
            domain=domain, fields=fields, limit=limit, offset=offset, order=order
        )

        return account_ids, len(all_account_ids)

    # incentive.report methods

    def search_latest_report_by_employee(self) -> dict:
        incentive_report_ids = self.search_incentive_report_by_employee()
        filtered_incentive_report_ids = filter_latest_event_by_status(
            incentive_report_ids
        )
        return filtered_incentive_report_ids

    def search_validate_report_by_employee(
        self,
    ) -> List[IncentiveReportSimpleSchema]:
        reports_ids = []
        incentive_report_ids = self.search_incentive_report_by_employee()
        for report in incentive_report_ids:
            if report["status"] == "done":
                reports_ids.append(
                    IncentiveReportSimpleSchema(
                        id=report["id"],
                        start_date=report["start_date"],
                        end_date=report["end_date"],
                        action=f"/api/v1/employee/report/{report['id']}/bonuses",
                    )
                )
        return reports_ids

    def search_inventive_report_by_id(self, report_id: int) -> IncentiveReportSchema:
        fields = list(IncentiveReportSchema.model_fields.keys())
        return self.model_incentive_report.search(
            [["id", "=", report_id]], fields=fields
        )

    def search_incentive_report_by_employee(
        self,
    ) -> List[IncentiveReportSchema]:
        fields = list(IncentiveReportSchema.model_fields.keys())
        generic_job_id = self.user_context["generic_job_id"][0]
        company_id = self.user_context["company_id"][0]
        incentive_report_ids = self.model_incentive_report.search(
            [["generic_job_id", "=", generic_job_id], ["company_id", "=", company_id]],
            fields=fields,
        )
        return incentive_report_ids

    # incentive.event methods

    def search_event_type(self):
        fields = list(EventTypeSchema.model_fields.keys())
        event_type_ids = self.move_event_type.search(domain=[], fields=fields)
        return event_type_ids

    @check_can_use_application_agent
    def search_bonuses(
        self,
        offset: int = 0,
        limit: int = -1,
        order: str = "event_date desc",
        event_date_start: Optional[date] = None,
        event_date_end: Optional[date] = None,
        report_id: Optional[int] = None,
    ) -> IncentiveEventSummarySchema:
        valid_report_ids = self.search_incentive_report_by_employee()
        employee_valid_report = list(map(lambda item: item["id"], valid_report_ids))
        if report_id and report_id not in employee_valid_report:
            return IncentiveEventSummarySchema(
                count=0, models="incentive.event", total_value=0, records=[]
            )
        # Constants
        employee_id = int(self.user_context["sub"])

        # Build domain filters
        domain = self._build_bonus_domain(
            employee_id=employee_id,
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            category=None,
            report_id=report_id,
        )
        if report_id:
            vals_report_id = list(
                filter(lambda item: item["id"] == report_id, valid_report_ids)
            )[0]
        # Fetch fields and records
        fields = list(IncentiveEventSchema.model_fields.keys())
        record_ids, total_count = self.model_incentive_event.model_method(
            "get_event_details",
            {
                "domain": domain,
                "fields": fields,
                "limit": limit,
                "offset": offset,
                "order": order,
            },
        )
        # Enrich records
        enriched_records, total_value = self._enrich_records(record_ids)

        return vals_report_id, IncentiveEventSummarySchema(
            event_categories=enriched_records, total_value=total_value
        )

    def _extract_color(self, value):
        red = "#e3350e"
        green = "#17871b"
        return red if value < 0 else green

    def fetch_bonuses_details_by_report(
        self,
        report_id,
        limit: Optional[int] = -1,
        offset: Optional[int] = 0,
        order: Optional[str] = "event_date desc",
        category: Optional[str] = None,
    ) -> IncentiveReportDetailsSchema:
        employee_id = self.user_context["sub"]
        domain = self._build_bonus_domain(
            employee_id=int(employee_id),
            category=category,
            report_id=report_id,
        )
        fields = list(IncentiveEventSchema.model_fields.keys())
        record_ids, total_count = self.model_incentive_event.model_method(
            "get_event_details",
            {
                "domain": domain,
                "fields": fields,
                "limit": limit,
                "offset": offset,
                "order": order,
            },
        )
        events = []
        currency = self.user_context["currency_id"][1]
        filter_value: List[FilterSchema] = []
        total_value = 0
        for record_id in record_ids:
            filter_id = FilterSchema(
                value=record_id["event_category"]["code"],
                param="event_category",
                label=record_id["event_category"]["name"],
            )
            if filter_id not in filter_value:
                filter_value.append(filter_id)

            value = record_id["value"]
            value_color = self._extract_color(value)
            client_id = record_id["client_id"]
            client_name = client_id["name"] if client_id.get("name") else "Unknown"
            category = record_id["event_category"]
            collapsed = CollapsedCardSchema(
                icon=category["icon"],
                icon_color=category["color"],
                title=client_name,
                value=value,
                currency=currency,
                value_color=value_color,
                subtitle=category["name"],
            )
            expanded = ExpandedSchema(
                rows=[
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Incentive type", fr="Type d'évènement"
                        ),
                        value=TextTranslationSchema(
                            en="New customer bonus", fr="Nouveau bonus client"
                        ),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Incentive criteria", fr="Critères de l'évènements"
                        ),
                        value=TextTranslationSchema(
                            en=record_id["event_date"], fr=record_id["event_date"]
                        ),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(en="Account", fr="Compte"),
                        value=TextTranslationSchema(
                            en="First time product purchase",
                            fr="Premier achat de produit",
                        ),
                    ),
                    RowSchema(
                        label=TextTranslationSchema(
                            en="Commission amount", fr="Montant de la commission"
                        ),
                        value=TextTranslationSchema(
                            en=f"{value} {currency}", fr=f"{value} {currency}"
                        ),
                    ),
                ]
            )
            events.append(
                CardSchema(
                    id=f"incentive_event_{record_id['event_id']}",
                    expanded=expanded,
                    collapsed=collapsed,
                )
            )
            total_value += value
        return IncentiveReportDetailsSchema(
            list_id=f"incentive_report_{report_id}",
            total_value=total_value,
            currency=currency,
            pagination=PaginationSchema(
                offset=offset,
                limit=limit,
                current_records=len(record_ids),
                total_records=total_count,
            ),
            filters=filter_value,
            cards=events,
        )

    def fetch_bonuses_summary_by_report(self, report_id) -> SummarySimpleSchema:
        vals_report_id, bonuses = self.search_bonuses(report_id=report_id)
        return SummarySimpleSchema(
            total_earnings=bonuses.total_value,
            categories=bonuses.event_categories,
            date_range=DateRangeSchema(
                start=vals_report_id["start_date"],
                end=vals_report_id["end_date"],
            ),
            currency=self.user_context["currency_id"][1],
            action=f"/api/v1/report/{report_id}/details",
        )

    def _build_bonus_domain(
        self,
        employee_id: int,
        event_date_start: Optional[date] = None,
        event_date_end: Optional[date] = None,
        category: Optional[List[str]] = None,
        report_id: Optional[int] = None,
    ) -> List:
        """Build the domain for searching incentive events."""
        domain = [
            ["beneficiary_employee_id", "=", employee_id],
            ["event_status", "in", ["validated", "calculated"]],
        ]
        if category:
            domain.append(["event_type_id.type_id.code", "in", [category]])
        if report_id:
            domain.append(["report_id", "=", report_id])
        else:
            if event_date_start:
                domain.append(
                    ["event_date", ">=", event_date_start.strftime("%Y-%m-%d")]
                )
            if event_date_end:
                domain.append(["event_date", "<=", event_date_end.strftime("%Y-%m-%d")])
        return domain

    def _enrich_records(self, record_ids: List[dict]) -> tuple:
        """Enrich records with event type and account details."""
        enriched_records = []
        total_value = 0
        event_type_value = dict()
        for record in record_ids:
            if record.get("event_category"):
                event_type = record["event_category"]
                event_type_name = event_type["name"]
                event_type_color = event_type["color"]
                event_type_code = event_type["code"]
                if event_type_name not in event_type_value:
                    event_type_value[event_type_name] = {
                        "value": 0,
                        "color": event_type_color,
                        "code": event_type_code,
                    }
                event_type_value[event_type_name]["value"] += record["value"]
            total_value += record["value"]
        for item in event_type_value:
            enriched_records.append(
                EventCategorySchema(
                    name=item,
                    color=event_type_value[item]["color"],
                    value=event_type_value[item]["value"],
                    code=event_type_value[item]["code"],
                )
            )
        sorted_records = sorted(enriched_records, key=lambda x: x.value, reverse=True)
        return (sorted_records, total_value)

    def _find_account_id(self, record: dict) -> List[dict]:
        """Find account details for a given record."""
        fields = list(PaygAccountSchema.model_fields.keys())
        account_id = self.model_payg_account.search(
            domain=[["id", "=", record["account_id"][0]]],
            fields=fields,
            limit=1,
        )
        return account_id

    def refresh_token(self, data: dict) -> TokenSchema:
        payload = data["payload"]
        logging.info(f"refresh_token Payload: {payload}")
        token = data["token"]
        employee_id = int(payload["sub"])
        self.check_refresh_token(employee_id, token)
        employee_details = self.search_employee_by_id(employee_id)
        employee_details.pop("id")
        employee_details["sub"] = employee_id
        access_token = create_access_token(employee_details)
        expire_in = settings.access_token_expire * 60
        refresh_token = create_refresh_token({"sub": employee_id})
        self.set_refresh_token(employee_id, refresh_token)
        return TokenSchema(
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
