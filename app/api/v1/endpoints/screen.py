from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.screen import SummarySchema, TasksSchema
from app.services.main import fetch_homepage
from app.services.main import get_homepage_tasks as fetch_homepage_tasks
from app.utils.main import verify_access_token

router = APIRouter()


@router.get(
    "/homepage",
    summary="Get Homepage",
    description="Returns ",
    responses={
        200: {
            "model": SummarySchema,
        }
    },
)
async def get_homepage(user_context=Depends(verify_access_token)):
    try:
        return fetch_homepage(user_context)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        return JSONResponse(content=e.args[0], status_code=500)


@router.get(
    "/homepage/tasks",
    summary="Get Homepage TasksSchema",
    description="""Returns a list of tasks displayed on the employee's homepage.
    Each task includes an icon, label, count, and an action URL.""",
    responses={
        200: {
            "model": List[TasksSchema],
            "description": "List of tasks for the employee's homepage.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "icon": "slow-payer-icon",
                            "label": "Slow payers",
                            "count": 4,
                            "action": "/api/v1/employee/slow-payers",
                        }
                    ]
                }
            },
        }
    },
)
async def get_homepage_tasks(user_context=Depends(verify_access_token)):
    try:
        return fetch_homepage_tasks(user_context)
    except ValueError as e:
        return JSONResponse(content=e.args[0], status_code=400)
    except Exception as e:
        return JSONResponse(content=e.args[0], status_code=500)
