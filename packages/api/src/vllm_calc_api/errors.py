"""The structured error contract and its exception handlers.

Every error response is `{"error": {"type", "message", "details"?}}` where type is
one of: validation, constraint_violation, unsupported, over_provision_estimate,
internal. (over_provision_estimate is carried as a result *flag*, not raised — see
Story 2.4 — so it does not appear here.)
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from vllm_calc_engine.exceptions import InvalidParallelism, UnsupportedArchitecture

__all__ = ["ErrorBody", "ErrorResponse", "register_exception_handlers"]


class ErrorBody(BaseModel):
    type: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def _error(status: int, type_: str, message: str, details: Any = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(type=type_, message=message, details=details))
    return JSONResponse(status_code=status, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(422, "validation", "Request body is invalid.", details=exc.errors())

    @app.exception_handler(InvalidParallelism)
    async def _parallelism(_: Request, exc: InvalidParallelism) -> JSONResponse:
        return _error(400, "constraint_violation", str(exc))

    @app.exception_handler(UnsupportedArchitecture)
    async def _unsupported(_: Request, exc: UnsupportedArchitecture) -> JSONResponse:
        return _error(400, "unsupported", str(exc))
