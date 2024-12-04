from fastapi import APIRouter

from .endpoints import employee, main, otp, screen

router = APIRouter()
router.include_router(screen.router, prefix="/screen", tags=["Screen"])
router.include_router(main.router, prefix="/ui", tags=["User Interface"])
router.include_router(otp.router, prefix="/otp", tags=["Authentication"])
router.include_router(employee.router, prefix="/employee", tags=["Employee"])
