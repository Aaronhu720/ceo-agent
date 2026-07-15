from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = ""
    error: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    message: str = ""


def success_response(data: Any = None, message: str = "") -> dict:
    return {"success": True, "data": data, "message": message}


def error_response(error: str, message: str = "") -> dict:
    return {"success": False, "error": error, "message": message}
