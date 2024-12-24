from collections import defaultdict
from typing import List

from app.schemas.incentive_event import (
    IncentiveEventMinimalRecord,
    IncentiveEventResponse,
)
from app.schemas.screen import DateRange, HomepageResponse, Summary, Tasks
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
        list: A list of IncentiveEventMinimalRecord objects grouped by category.
    """
    grouped_data = defaultdict(float)
    for record in records:
        grouped_data[record.event_type_id.category] += record.value
    return [
        IncentiveEventMinimalRecord(category=category, sum_value=value)
        for category, value in grouped_data.items()
    ]


def _get_currency_from_records(records):
    """
    Extract the currency ID from a list of records, if available.

    Args:
        records (list): A list of incentive event records.

    Returns:
        str: The currency ID, or None if no records are available.
    """
    return records[0].currency_id if records else None


def _get_summary_details(odoo_service: OdooService, current_report_id: int):
    # Fetch incentive events
    if current_report_id:
        bonues_ids = odoo_service.search_bonuses(report_id=current_report_id["id"])
    else:
        bonues_ids = IncentiveEventResponse(
            count=0, models="incentive.event", records=[]
        )
    # Process incentive events
    summary_details = _group_incentive_events_by_category(bonues_ids.records)
    currency_id = _get_currency_from_records(bonues_ids.records)
    total_value = sum([record.value for record in bonues_ids.records])
    return Summary(
        date_range=DateRange(
            start=current_report_id["start_date"], end=current_report_id["end_date"]
        ),
        total_earnings=total_value,
        currency=currency_id,
        details=summary_details,
        action="/api/v1",
        event_count=len(summary_details),
    )


def get_homepage_action(user_context: dict) -> str:
    return {
        "current_bonuses": "/api/v1/employee/bonuses?period=current",
        "previous_bonuses": "/api/v1/employee/bonuses?period=previous",
        "custom_bonuses": "/api/v1/employee/report",
        "tasks_list": "api/v1/homepage/tasks",
    }


def get_screen_homepage(user_context: dict) -> HomepageResponse:
    """
    Generate the dashboard response for the home page based on the employee ID and week offset.

    Args:
        employee_id (int): The employee's unique ID.
        week_offset (int): Week offset for the range of incentive events (default is 0).

    Returns:
        HomepageResponse: The structured response for the dashboard.
    """

    odoo_service = OdooService(user_context)
    # Fetch incentive reports
    latest_report_ids = odoo_service.search_latest_report_by_employee()
    current_report_id = latest_report_ids.get("in_progress", False)

    # Create the summary
    summary = _get_summary_details(odoo_service, current_report_id)

    return HomepageResponse(summary=summary)


def get_homepage_tasks(user_context: dict) -> List[Tasks]:
    """
    Build a list of dashboard components based on data retrieved from Odoo.

    Args:
        odoo_service (OdooService): Instance of OdooService to fetch data.
        employee_id (int): The employee's unique ID.

    Returns:
        list: A list of Tasks objects for the dashboard.
    """
    odoo_service = OdooService(user_context)
    account_ids = odoo_service.search_account_by_segmentation_and_responsible(
        offset=0, limit=-1, order="id desc"
    )
    return [
        Tasks(
            icon="slow-payer-icon",
            label="Slow payers",
            count=len(account_ids),
            action="/api/v1/employee/slow-payers",
        ),
    ]
