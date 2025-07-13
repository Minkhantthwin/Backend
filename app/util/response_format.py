from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

"""
########################
# Fastapi Status Codes
########################
#
# HTTP_100_CONTINUE = 100
# HTTP_101_SWITCHING_PROTOCOLS = 101
# HTTP_102_PROCESSING = 102
# HTTP_200_OK = 200
# HTTP_201_CREATED = 201
# HTTP_202_ACCEPTED = 202
# HTTP_204_NO_CONTENT = 204
# HTTP_205_RESET_CONTENT = 205
# HTTP_206_PARTIAL_CONTENT = 206
#
# HTTP_300_MULTIPLE_CHOICES = 300
# HTTP_301_MOVED_PERMANENTLY = 301
# HTTP_302_FOUND = 302
# HTTP_304_NOT_MODIFIED = 304
# HTTP_305_USE_PROXY = 305
# HTTP_306_RESERVED = 306
# HTTP_307_TEMPORARY_REDIRECT = 307
# HTTP_308_PERMANENT_REDIRECT = 308
#
# HTTP_400_BAD_REQUEST = 400
# HTTP_401_UNAUTHORIZED = 401
# HTTP_402_PAYMENT_REQUIRED = 402
# HTTP_403_FORBIDDEN = 403
# HTTP_404_NOT_FOUND = 404
# HTTP_405_METHOD_NOT_ALLOWED = 405
# HTTP_406_NOT_ACCEPTABLE = 406
# HTTP_407_PROXY_AUTHENTICATION_REQUIRED = 407
# HTTP_408_REQUEST_TIMEOUT = 408
# HTTP_421_MISDIRECTED_REQUEST = 421
# HTTP_423_LOCKED = 423
#
# HTTP_502_BAD_GATEWAY = 502
# HTTP_503_SERVICE_UNAVAILABLE = 503
# HTTP_504_GATEWAY_TIMEOUT = 504
# HTTP_505_HTTP_VERSION_NOT_SUPPORTED = 505
"""


class ResponseFormat(BaseModel):
    error: int = Field(
        0,
        description="Error code (0 for success, 100-200 for validation errors, 500-600 for internal errors).",
    )
    timestamp: Optional[str] = Field(None, description="Timestamp of the response.")
    message: str = Field(..., description="Response message.")
    data: Optional[Any] = Field(None, description="Response data.")

    def set_error(self, error_code: int, message: Optional[str] = None):
        self.error = error_code
        self.timestamp = datetime.now() if error_code != 0 else None
        if message:
            self.message = message

    @classmethod
    def failed_response(
        cls,
        message: str,
        error: int = 500,
        timestamp: Optional[datetime] = None,
        data: Optional[Any] = None,
    ) -> dict:
        dt = datetime.now()
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            error=error,
            timestamp=timestamp or dt_str,
            message=message,
            data=data,
        ).model_dump()

    @classmethod
    def success_response(
        cls,
        message: str = "Operation successful.",
        timestamp: Optional[datetime] = None,
        data: Optional[Any] = None,
    ) -> dict:
        dt = datetime.now()
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            error=0,
            timestamp=timestamp or dt_str,
            message=message,
            data=data,
        ).model_dump()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # Convert datetime to ISO 8601 format
        }
