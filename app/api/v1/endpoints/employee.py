from typing import List

from fastapi import APIRouter, Depends, Query

from app.schemas.error import ErrorResponse
from app.schemas.incentive_event import IncentiveEventResponse
from app.schemas.incentive_report import IncentiveReportSimple, ReportPeriod
from app.schemas.payg_account import PaygAccountResponse
from app.services.odoo.service import OdooService
from app.utils.main import (
    get_column_order,
    handle_exceptions_employee,
    validate_order,
    verify_access_token,
)

router = APIRouter()


@router.get(
    "/bonuses",
    summary="Get Bonuses by Employee ID",
    description="""Retrieves a list of incentive events (bonuses) for a specific employee during a given period.
    The endpoint returns details like event date, value, and associated client information.""",
    responses={
        200: {
            "model": IncentiveEventResponse,
            "description": "List of incentive events for the employee.",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request or missing parameters.",
        },
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
async def get_bonus_by_employee_id(
    period: ReportPeriod,
    user_context: dict = Depends(verify_access_token),
) -> IncentiveEventResponse:
    service = OdooService(user_context)
    return service.search_bonuses_by_employee(period)


@router.get(
    "/report",
    summary="Get Validated Reports by Employee",
    description="""Returns a list of validated reports for the authenticated employee.
    Each report provides basic information like the report ID and relevant dates.""",
    responses={
        200: {
            "model": List[IncentiveReportSimple],
            "description": "List of validated reports for the employee.",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request or missing parameters.",
        },
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
async def get_custom_bonus_by_employee_id(
    user_context: dict = Depends(verify_access_token),
) -> List[IncentiveReportSimple]:
    service = OdooService(user_context)
    report_ids = service.search_validate_report_by_employee()
    return report_ids


@router.get(
    "/report/{report_id}/bonuses",
    summary="Get Bonus Report by ID",
    description="""Fetches detailed bonus information for a specific report ID.
    Returns incentive events linked to that report, including event date, value, and client details.""",
    responses={
        200: {
            "model": IncentiveEventResponse,
            "description": "List of incentive events for the given report ID.",
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid report ID or request format.",
        },
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
async def get_bonus_report_by_id(
    report_id: int,
    user_context: dict = Depends(verify_access_token),
) -> IncentiveEventResponse:
    service = OdooService(user_context)
    return service.search_bonuses(report_id=report_id)


@router.get(
    "/slower-payer",
    response_model=PaygAccountResponse,
    summary="Retrieve slow-paying clients by employee",
    description=(
        "Fetch a paginated list of clients identified as slow payers, "
        "managed by a specific responsible employee. "
        "Results can be sorted and paginated."
    ),
    responses={
        200: {
            "description": "List of account records retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "count": 2,
                        "models": "payg.account",
                        "records": [
                            {
                                "id": 1,
                                "account_ext_id": "ACC12345",
                                "create_date": "2023-12-20T09:26:07",
                                "client_id": {"id": 101, "name": "Acme Corporation"},
                            },
                            {
                                "id": 2,
                                "account_ext_id": "ACC54321",
                                "create_date": "2023-12-18T14:15:00",
                                "client_id": {"id": 102, "name": "Global Industries"},
                            },
                        ],
                    }
                }
            },
        },
        403: {"description": "Unauthorized access to the employee's data."},
        404: {"description": "Employee not found."},
        500: {"description": "Internal server error."},
    },
)
async def get_slower_payer_client(
    offset: int = 0,
    limit: int = 80,
    order: str = Query(
        "create_date desc", description="Format: 'column asc' or 'column desc'"
    ),
    user_context: dict = Depends(verify_access_token),
):
    service = OdooService()
    order = validate_order(order, get_column_order())
    return service.get_slower_payer_client_service(
        user_context["user_id"], offset, limit, order
    )


get_bonus_by_employee_id = handle_exceptions_employee(get_bonus_by_employee_id)

get_custom_bonus_by_employee_id = handle_exceptions_employee(
    get_custom_bonus_by_employee_id
)
get_slower_payer_client = handle_exceptions_employee(get_slower_payer_client)
get_bonus_report_by_id = handle_exceptions_employee(get_bonus_report_by_id)
