from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.schemas.error import ErrorSchema
from app.schemas.global_schema import TaskSchema
from app.schemas.incentive_event import IncentiveEventSummarySchema
from app.schemas.incentive_report import (
    IncentiveReportDetailsSchema,
    IncentiveReportSimpleSchema,
)
from app.schemas.screen import SummarySimpleSchema
from app.schemas.user import UserSchema
from app.services.odoo.exceptions import EmployeeNotFoundException
from app.services.odoo.service import OdooService
from app.utils.main import verify_access_token

router = APIRouter()


@router.get(
    "/",
    summary="Get Employee Account Details",
    description="""Fetches the account details for the authenticated employee.
    The response includes information like the employee's name, loyality points, phone number, etc.""",
    responses={
        200: {"model": UserSchema},
        400: {
            "model": ErrorSchema,
            "description": "Invalid request or missing parameters.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_employee_profile(
    user_context: dict = Depends(verify_access_token),
):
    try:
        service = OdooService(user_context)
        return service.get_employee_profile()
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except EmployeeNotFoundException as e:
        return JSONResponse(content=e.args[0], status_code=404)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.get(
    "/report",
    summary="Get Validated Reports by Employee",
    description="""Returns a list of validated reports for the authenticated employee.
    Each report provides basic information like the report ID and relevant dates.""",
    responses={
        200: {
            "model": List[IncentiveReportSimpleSchema],
            "description": "List of validated reports for the employee.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid request or missing parameters.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_custom_bonus_by_employee_id(
    user_context: dict = Depends(verify_access_token),
) -> List[IncentiveReportSimpleSchema]:
    try:
        service = OdooService(user_context)
        report_ids = service.search_validate_report_by_employee()
        return report_ids
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.get(
    "/report/{report_id}/summary",
    summary="Get Bonus Report by ID",
    description="""Fetch the summary of a bonus report. The summary includes the total amount to retain,
    a breakdown by bonus category, the report date, and the color codes.""",
    responses={
        200: {
            "model": IncentiveEventSummarySchema,
            "description": "List of incentive events for the given report ID.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid report ID or request format.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_bonus_report_by_id(
    report_id: int,
    user_context: dict = Depends(verify_access_token),
) -> SummarySimpleSchema:
    try:
        service = OdooService(user_context)
        return service.fetch_bonuses_summary_by_report(report_id=report_id)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.get(
    "/report/{report_id}/details",
    summary="Get Bonus Report Details",
    description="""Fetch the details of a report by listing each event in the report along with
    the information of the accounts that generated the bonus.""",
    responses={
        200: {
            "model": IncentiveReportDetailsSchema,
            "description": "List of incentive events for the given report ID.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid report ID or request format.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_bonuses_details(
    report_id: int,
    category: int = Query(None, description="ID of event type"),
    user_context: dict = Depends(verify_access_token),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    limit: int = Query(10, description="Number of records to fetch", ge=10, le=100),
) -> IncentiveReportDetailsSchema:
    try:
        service = OdooService(user_context)
        return service.fetch_bonuses_details_by_report(
            report_id=report_id,
            category=category,
            offset=offset,
            limit=limit,
        )
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.get(
    "/tasks/slow-payers",
    summary="Get Slow Payers",
    description="""Returns a list of slow payers for the authenticated employee.""",
    responses={
        200: {
            "model": TaskSchema,
            "description": "List of Slow payer for the current user.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid report ID or request format.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_slow_payer(
    user_context=Depends(verify_access_token),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    limit: int = Query(10, description="Number of records to fetch", ge=10, le=100),
    day_late: Optional[Literal["new", "urgent"]] = Query(
        None, description="Filter by 'new' or 'urgent'"
    ),
) -> TaskSchema:
    try:
        service = OdooService(user_context)
        return service.get_slower_payer_client_service(
            limit=limit, offset=offset, day_late=day_late
        )
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)


@router.get(
    "/tasks/hypercare",
    summary="Get Hypercare",
    description="""Returns a list of hypercare at risk for the authenticated employee.""",
    responses={
        200: {
            "model": TaskSchema,
            "description": "List of hypercare at risk for the current user.",
        },
        400: {
            "model": ErrorSchema,
            "description": "Invalid report ID or request format.",
        },
        401: {
            "model": ErrorSchema,
            "description": "Unauthorized access. Please provide a valid access token.",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
async def get_hypercare_at_risk(
    user_context=Depends(verify_access_token),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    limit: int = Query(10, description="Number of records to fetch", ge=10, le=100),
) -> TaskSchema:
    try:
        service = OdooService(user_context)
        return service.get_hypercare_at_risk_service(limit=limit, offset=offset)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)
