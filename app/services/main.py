from collections import defaultdict
from typing import List

from app.schemas.incentive_event import IncentiveEventMinimalSchema
from app.schemas.screen import DateRangeSchema, SummarySchema, TasksSchema
from app.services.odoo.service import OdooService

# Constants for country data
AVAILABLE_COUNTRIES = [
    {
        "name": "Nigeria",
        "flag_url": "https://flagcdn.com/w320/ng.png",
        "dial_code": "+234",
    },
    {
        "name": "Ivory Coast",
        "flag_url": "https://flagcdn.com/w320/ci.png",
        "dial_code": "+225",
    },
    {
        "name": "Madagascar",
        "flag_url": "https://flagcdn.com/w320/mg.png",
        "dial_code": "+261",
    },
    {
        "name": "Senegal",
        "flag_url": "https://flagcdn.com/w320/sn.png",
        "dial_code": "+221",
    },
]


def get_available_country():
    """
    Fetch a list of available countries with details such as name, flag URL, and dial code.
    """
    return AVAILABLE_COUNTRIES


def _group_incentive_events_by_category(records):
    """
    Group incentive events by category and calculate the sum of values for each category.

    Args:
        records (list): A list of incentive event records.

    Returns:
        list: A list of IncentiveEventMinimalSchema objects grouped by category.
    """
    grouped_data = defaultdict(float)
    for record in records:
        grouped_data[record.event_type_id.category] += record.value
    return [
        IncentiveEventMinimalSchema(category=category, sum_value=value)
        for category, value in grouped_data.items()
    ]


def fetch_homepage(user_context: dict) -> SummarySchema:
    odoo_service = OdooService(user_context)
    status = "in_progress"
    latest_report_ids = odoo_service.search_latest_report_by_employee()
    if not latest_report_ids:
        return SummarySchema(
            total_earnings=0,
            categories=[],
            date_range=DateRangeSchema(),
            currency=user_context["currency_id"][1],
            action="",
            current_report_id=0,
            last_report_id=0,
        )
    current_report_id = latest_report_ids.get(status, False)
    latest_report_id = latest_report_ids.get("done", False)
    vals_report_id, bonuses = odoo_service.search_bonuses(
        report_id=current_report_id["id"]
    )
    report_id = current_report_id["id"]
    return SummarySchema(
        total_earnings=bonuses.total_value,
        categories=bonuses.event_categories,
        date_range=DateRangeSchema(
            start=current_report_id["start_date"],
            end=current_report_id["end_date"],
        ),
        currency=user_context["currency_id"][1],
        action=f"/api/v1/report/{report_id}/details",
        current_report_id=report_id,
        last_report_id=latest_report_id["id"],
    )


def get_homepage_tasks(user_context: dict) -> List[TasksSchema]:
    """
    Build a list of dashboard components based on data retrieved from Odoo.

    Args:
        odoo_service (OdooService): Instance of OdooService to fetch data.
        employee_id (int): The employee's unique ID.

    Returns:
        list: A list of TasksSchema objects for the dashboard.
    """
    odoo_service = OdooService(user_context)
    return odoo_service.get_employee_tasks()
