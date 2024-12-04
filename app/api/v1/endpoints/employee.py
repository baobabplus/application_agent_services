from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Query  # ,Depends

from app.schemas.employee import EmployeeSchema
from app.schemas.incentive_event import IncentiveEventResponse
from app.schemas.payg_account import PaygAccountResponse
from app.schemas.prospect import ProspectResponse
from app.services.odoo.exceptions import (
    EmployeeNotFoundException,
    UnauthorizedEmployeeException,
)
from app.services.odoo.service import OdooService
from app.utils.main import get_column_order, validate_order  # verify_jwt

router = APIRouter()


@router.get(
    "/{phone_number}",
    response_model=List[EmployeeSchema],
    summary="Get odoo employee by phone number",
    description=(
        "This endpoint retrieves the details of an employee from the Odoo system "
        "based on the provided unique phone number. The response includes detailed "
        "employee information such as ID, name, phone number, department, and position."
    ),
    responses={
        200: {
            "description": "The employee details matching the phone number.",
            "content": {"application/json": {"example": {"id": 1, "name": "John Doe"}}},
        },
        404: {
            "description": "Employee not found for the provided phone number.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Employee with phone number +123456789 not found."
                    }
                }
            },
        },
        500: {
            "description": "Server error. Could not retrieve the employee.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while processing the request."
                    }
                }
            },
        },
    },
)
async def get_employee_by_phone_number(phone_number: str):
    try:
        service = OdooService()
        return service.search_employee_by_phone(phone_number)
    except UnauthorizedEmployeeException as e:
        raise HTTPException(status_code=403, detail=e.details)
    except EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.details)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=e.args[0]["details"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{employee_id}/bonuses",
    response_model=IncentiveEventResponse,
    summary="Retrieve bonuses for a specific employee",
    description=(
        "Fetch a paginated list of bonuses for a given employee. "
        "You can filter results by date range (`event_date_start` and `event_date_end`) "
        "and sort them using the `order` parameter."
    ),
    responses={
        200: {
            "description": "List of bonuses retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "count": 8,
                        "models": "incentive.event",
                        "records": [
                            {
                                "id": 1,
                                "event_date": "2024-09-25",
                                "value": 2000,
                                "currency_id": {"id": 105, "display_name": "MGA"},
                                "event_type_id": {
                                    "id": 6,
                                    "name": "75-PERCENT-PAID",
                                    "category": "Payment",
                                },
                                "account_id": {
                                    "id": 2,
                                    "account_ext_id": "AC9354564",
                                    "create_date": "2023-11-25T13:08:04",
                                    "client_id": {"id": 6, "display_name": "Jone Doe"},
                                },
                            },
                            {
                                "id": 9,
                                "event_date": "2024-09-25",
                                "value": 300,
                                "currency_id": {"id": 105, "display_name": "MGA"},
                                "event_type_id": {
                                    "id": 27,
                                    "name": "RPP",
                                    "category": "RPP",
                                },
                                "account_id": {
                                    "id": 888,
                                    "account_ext_id": "AC11584444",
                                    "create_date": "2024-09-14T06:03:51",
                                    "client_id": {
                                        "id": 5432,
                                        "display_name": "Lorem Ipsum",
                                    },
                                },
                            },
                        ],
                    }
                }
            },
        },
        403: {"description": "Unauthorized access to the employee's bonuses."},
        404: {"description": "Employee not found."},
        500: {"description": "Internal server error."},
    },
)
async def get_bonus_by_employee_id(
    employee_id: int,
    offset: int = 0,
    limit: int = 80,
    order: str = Query(
        "event_date desc", description="Format: 'column asc' or 'column desc'"
    ),
    event_date_start: date = Query(
        None, description="Filter by event date start (YYYY-MM-DD)"
    ),
    event_date_end: date = Query(
        None, description="Filter by event date end (YYYY-MM-DD)"
    ),
    # user_context: dict = Depends(verify_jwt)
):
    try:
        service = OdooService()
        order = validate_order(order, get_column_order(["event_date"]))
        return service.search_bonus_by_employee(
            employee_id, offset, limit, order, event_date_start, event_date_end
        )
    except UnauthorizedEmployeeException as e:
        raise HTTPException(status_code=403, detail=e.details)
    except EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{employee_id}/slower-payer",
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
    employee_id: int,
    offset: int = 0,
    limit: int = 80,
    order: str = Query(
        "create_date desc", description="Format: 'column asc' or 'column desc'"
    ),
):
    try:
        service = OdooService()
        order = validate_order(order, get_column_order())
        return service.search_slower_payer_employee(employee_id, offset, limit, order)
    except UnauthorizedEmployeeException as e:
        raise HTTPException(status_code=403, detail=e.details)
    except EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{employee_id}/prospects",
    response_model=ProspectResponse,
    summary="Retrieve prospects by responsible employee",
    description=(
        "Fetch a paginated list of prospects managed by a specific responsible employee. "
        "The results include details such as the prospect's external ID, creation date, "
        "and current state."
    ),
    responses={
        200: {
            "description": "List of prospect records retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "count": 2,
                        "models": "prospect",
                        "records": [
                            {
                                "id": 1,
                                "prospect_ext_id": "PROS12345",
                                "create_date": "2023-12-20T09:26:07",
                                "state": "APPROVED",
                            },
                            {
                                "id": 2,
                                "prospect_ext_id": "PROS54321",
                                "create_date": "2023-12-19T15:45:00",
                                "state": False,
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
async def get_prospect_by_responsible_employee_id(
    employee_id: int,
    offset: int = 0,
    limit: int = 80,
    order: str = Query(
        "create_date desc", description="Format: 'column asc' or 'column desc'"
    ),
):
    try:
        service = OdooService()
        order = validate_order(order, get_column_order())
        return service.search_prospect_by_responsible_employee(
            employee_id, offset, limit, order
        )
    except UnauthorizedEmployeeException as e:
        raise HTTPException(status_code=403, detail=e.details)
    except EmployeeNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
