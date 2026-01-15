"""
响应工具
创建日期: 2025-01-08
用途: 统一响应格式
"""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel
from fastapi import Response
from fastapi.responses import JSONResponse


class ApiResponse(BaseModel):
    """API统一响应格式"""

    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {"code": self.code, "message": self.message, "data": self.data}


def success_response(
    data: Any = None, message: str = "success", code: int = 200
) -> ApiResponse:
    """成功响应"""
    return ApiResponse(code=code, message=message, data=data)


def error_response(
    message: str = "error", code: int = 400, data: Any = None
) -> ApiResponse:
    """错误响应"""
    return ApiResponse(code=code, message=message, data=data)


def paginated_response(
    items: List[Any], total: int, page: int, size: int, message: str = "success"
) -> ApiResponse:
    """分页响应"""
    pages = (total + size - 1) // size
    data = {"items": items, "total": total, "page": page, "size": size, "pages": pages}
    return ApiResponse(code=200, message=message, data=data)


class ResponseUtil:
    """响应工具类"""

    @staticmethod
    def success(data: Any = None, message: str = "success", code: int = 200) -> dict:
        """成功响应"""
        return success_response(data, message, code).to_dict()

    @staticmethod
    def error(message: str = "error", code: int = 400, data: Any = None) -> dict:
        """错误响应"""
        return error_response(message, code, data).to_dict()

    @staticmethod
    def paginated(
        items: List[Any], total: int, page: int, size: int, message: str = "success"
    ) -> dict:
        """分页响应"""
        return paginated_response(items, total, page, size, message).to_dict()

    @staticmethod
    def created(data: Any = None, message: str = "创建成功") -> dict:
        """创建成功响应"""
        return success_response(data, message, 201).to_dict()

    @staticmethod
    def updated(data: Any = None, message: str = "更新成功") -> dict:
        """更新成功响应"""
        return success_response(data, message, 200).to_dict()

    @staticmethod
    def deleted(message: str = "删除成功") -> dict:
        """删除成功响应"""
        return success_response(None, message, 200).to_dict()

    @staticmethod
    def not_found(message: str = "资源不存在") -> dict:
        """资源不存在响应"""
        return error_response(message, 404).to_dict()

    @staticmethod
    def unauthorized(message: str = "未授权访问") -> dict:
        """未授权响应"""
        return error_response(message, 401).to_dict()

    @staticmethod
    def forbidden(message: str = "权限不足") -> dict:
        """权限不足响应"""
        return error_response(message, 403).to_dict()

    @staticmethod
    def validation_error(message: str = "参数验证失败", data: Any = None) -> dict:
        """参数验证失败响应"""
        return error_response(message, 422, data).to_dict()


# 快捷函数
success = ResponseUtil.success
error = ResponseUtil.error
paginated = ResponseUtil.paginated
created = ResponseUtil.created
updated = ResponseUtil.updated
deleted = ResponseUtil.deleted
not_found = ResponseUtil.not_found
unauthorized = ResponseUtil.unauthorized
forbidden = ResponseUtil.forbidden
validation_error = ResponseUtil.validation_error
