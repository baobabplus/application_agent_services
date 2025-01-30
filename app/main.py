from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.api.v1 import router as api_v1_router


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Baobab API",
        version="1.0.0",
        description="API for Baobabplus mobile application",
        routes=app.routes,
    )
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            responses = openapi_schema["paths"][path][method]["responses"]
            if "422" in responses:
                responses["422"] = {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "error": "validation_error",
                                "error_description": "Detailed description of the error",
                            }
                        }
                    },
                }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "error_description": str(exc._errors[0]),
        },
    )


@app.exception_handler(Exception)
async def internal_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_servor_error",
            "error_description": str(exc),
        },
    )


app.include_router(api_v1_router, prefix="/api/v1")
app.openapi = custom_openapi
