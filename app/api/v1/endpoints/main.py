from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.country import CountrySchema
from app.schemas.error import ErrorSchema
from app.services.main import get_available_country as fetch_available_country

router = APIRouter()


@router.get(
    "/available-country",
    summary="Get list of available countries",
    description="""
This endpoint retrieves a list of available countries.

The response includes:

- The name of each country.
- A URL to the flag of the country.
- The dialing code (country code).

This data can be used for rendering dropdowns or selection lists in the UI.
    """,
    responses={
        200: {
            "model": List[CountrySchema],
            "description": "List of available country",
        },
        500: {"model": ErrorSchema, "description": "Internal server error."},
    },
)
def get_available_country() -> List[CountrySchema]:
    try:
        return fetch_available_country()
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        err_value = {
            "error": "internal_server_error",
            "error_description": str(e),
        }
        return JSONResponse(content=err_value, status_code=500)
