from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.schemas.employee import EmployeeSchema
from app.schemas.payg_account import PaygAccountResponse
from app.schemas.prospect import ProspectResponse
from app.services.odoo.service import OdooService
from app.utils.main import (
    generate_slow_payer_description,
    get_column_order,
    validate_order,
)

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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=e.args[0]["details"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}/bonus")
async def get_bonus_by_employee_id(
    employee_id: int,
    offset: int = 0,
    limit: int = 80,
    order: str = Query(
        "event_date desc", description="Format: 'column asc' or 'column desc'"
    ),
):
    try:
        service = OdooService()
        order = validate_order(order, get_column_order(["event_date"]))
        return service.search_bonus_by_employee(employee_id, offset, limit, order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{employee_id}/slower-payer",
    response_model=PaygAccountResponse,
    summary="Retrieving the list of clients who are slow payers by responsible employee.",
    description=generate_slow_payer_description(),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}/prospect", response_model=ProspectResponse)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
