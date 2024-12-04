from fastapi import APIRouter, HTTPException

from app.schemas.screen import DashboardResponse
from app.services.main import BaseAPI

router = APIRouter()


@router.get(
    "/homepage/{employee_id}",
    response_model=DashboardResponse,
)
async def get_screen_home_page(employee_id: int):
    try:
        base_api = BaseAPI()
        return base_api.get_screen_home_page(employee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
