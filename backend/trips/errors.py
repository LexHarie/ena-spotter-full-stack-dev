from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _first_detail(value) -> str:
    if isinstance(value, dict):
        return _first_detail(next(iter(value.values()), "Invalid value."))
    if isinstance(value, list):
        return _first_detail(value[0] if value else "Invalid value.")
    return str(value)


def error_response(
    code: str,
    message: str,
    *,
    status_code: int,
    field: str | None = None,
    retryable: bool = False,
) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "field": field,
                "retryable": retryable,
            }
        },
        status=status_code,
    )


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected server error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True,
        )
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        field = next(iter(response.data), None) if isinstance(response.data, dict) else None
        detail = response.data.get(field) if field else response.data
        return error_response(
            "VALIDATION_ERROR",
            _first_detail(detail),
            status_code=response.status_code,
            field=field,
        )
    return response
