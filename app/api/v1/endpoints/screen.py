from typing import List

from fastapi import APIRouter, Depends

from app.schemas.screen import Tasks
from app.services.main import get_homepage_action
from app.services.main import get_homepage_tasks as fetch_homepage_tasks
from app.utils.main import handle_exceptions, verify_access_token

router = APIRouter()


@router.get(
    "/homepage",
    summary="Get Homepage Actions",
    description="Returns URLs for various sections on the employee's homepage, including bonuses and tasks.",
    responses={
        200: {
            "description": "Homepage URLs for the employee.",
            "content": {
                "application/json": {
                    "example": {
                        "current_bonuses": "/api/v1/employee/bonuses?period=current",
                        "previous_bonuses": "/api/v1/employee/bonuses?period=previous",
                        "custom_bonuses": "/api/v1/employee/report",
                        "tasks_list": "api/v1/homepage/tasks",
                    }
                }
            },
        }
    },
)
async def get_screen_homepage(user_context=Depends(verify_access_token)):
    return get_homepage_action(user_context)


@router.get(
    "/homepage/tasks",
    summary="Get Homepage Tasks",
    description="""Returns a list of tasks displayed on the employee's homepage.
    Each task includes an icon, label, count, and an action URL.""",
    responses={
        200: {
            "model": List[Tasks],
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
    return fetch_homepage_tasks(user_context)


get_screen_homepage = handle_exceptions(get_screen_homepage)

get_homepage_tasks = handle_exceptions(get_homepage_tasks)
