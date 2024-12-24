from fastapi import APIRouter, HTTPException

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
)
def get_available_country():
    try:
        return fetch_available_country()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
