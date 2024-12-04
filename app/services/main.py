from collections import defaultdict

from app.schemas.incentive_event import IncentiveEventMinimalRecord
from app.schemas.screen import Component, DashboardResponse, DateRange, Summary
from app.services.odoo.service import OdooService
from app.utils.main import get_week_range

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


class BaseAPI:
    def get_available_country(self):
        """
        Fetch a list of available countries with details such as name, flag URL, and dial code.
        """
        return {"count": len(AVAILABLE_COUNTRIES), "records": AVAILABLE_COUNTRIES}

    def get_screen_home_page(
        self, employee_id: int, week_offset: int = 0
    ) -> DashboardResponse:
        """
        Generate the dashboard response for the home page based on the employee ID and week offset.

        Args:
            employee_id (int): The employee's unique ID.
            week_offset (int): Week offset for the range of incentive events (default is 0).

        Returns:
            DashboardResponse: The structured response for the dashboard.
        """
        start_date, end_date = get_week_range(week_offset)
        odoo_service = OdooService()

        # Fetch incentive events
        incentive_event_response = self._fetch_incentive_events(
            odoo_service, employee_id, start_date, end_date
        )

        # Process incentive events
        summary_details = self._group_incentive_events_by_category(
            incentive_event_response.records
        )
        currency_id = self._get_currency_from_records(incentive_event_response.records)

        # Create the summary
        summary = Summary(
            date_range=DateRange(start=start_date, end=end_date),
            total_earnings=incentive_event_response.total_value,
            currency=currency_id,
            details=summary_details,
            action=f"/api/v1/employee/{employee_id}/bonuses/details",
            event_count=len(summary_details),
        )

        # Build the dashboard response
        components = self._get_dashboard_components(odoo_service, employee_id)
        return DashboardResponse(summary=summary, components=components)

    def _fetch_incentive_events(self, odoo_service, employee_id, start_date, end_date):
        """
        Fetch incentive events for a given employee within a specified date range.

        Args:
            odoo_service (OdooService): Instance of OdooService to fetch data.
            employee_id (int): Employee ID to filter records.
            start_date (str): Start date of the range.
            end_date (str): End date of the range.

        Returns:
            object: Response object containing incentive event records.
        """
        return odoo_service.search_bonus_by_employee(
            employee_id=employee_id,
            offset=0,
            limit=-1,
            order="id desc",
            event_date_start=start_date,
            event_date_end=end_date,
        )

    def _group_incentive_events_by_category(self, records):
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

    def _get_currency_from_records(self, records):
        """
        Extract the currency ID from a list of records, if available.

        Args:
            records (list): A list of incentive event records.

        Returns:
            str: The currency ID, or None if no records are available.
        """
        return records[0].currency_id if records else None

    def _get_dashboard_components(self, odoo_service: OdooService, employee_id: int):
        """
        Build a list of dashboard components based on data retrieved from Odoo.

        Args:
            odoo_service (OdooService): Instance of OdooService to fetch data.
            employee_id (int): The employee's unique ID.

        Returns:
            list: A list of Component objects for the dashboard.
        """
        account_ids = odoo_service.search_account_by_segmentation_and_responsible(
            employee_id, offset=0, limit=-1, order="id desc"
        )
        prospect_ids = odoo_service.search_prospect_by_responsible_employee(
            employee_id, offset=0, limit=-1, order="id desc"
        )
        return [
            Component(
                icon="slow-payer-icon",
                label="Slow payers",
                count=len(account_ids),
                action=f"/api/v1/employee/{employee_id}/slow-payers",
            ),
            Component(
                icon="prospects-icon",
                label="Prospects",
                count=len(prospect_ids),
                action=f"/api/v1/employee/{employee_id}/prospects",
            ),
        ]
