import logging
from rest_framework import exceptions, status
from rest_framework.response import Response

logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info_logger")
logger_error = logging.getLogger("error_logger")


class HandleException:
    """
    Mixin to handle exceptions and return a consistent response structure for different error types.
    """

    def handle_exception(self, exc):
        """
        Handles various exceptions and returns an appropriate response.

        Returns:
            Response: A DRF Response object with a standardized error message and HTTP status code.
        """
        if isinstance(exc, exceptions.AuthenticationFailed):
            logger_error.error(f"AuthenticationFailed: {exc}")
            return Response(
                {
                    "status": False,
                    "message": exc.default_detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(exc, exceptions.NotAuthenticated):
            logger_error.error(f"NotAuthenticated: {exc}")
            return Response(
                {
                    "status": False,
                    "message": exc.detail,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if isinstance(exc, exceptions.PermissionDenied):
            logger_error.error(f"PermissionDenied: {exc}")
            return Response(
                {
                    "status": False,
                    "message": exc.detail,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if isinstance(exc, exceptions.ValidationError):
            logger_error.error(f"ValidationError: {exc}")
            try:
                message = exc.detail[next(iter(exc.detail))][0]
            except Exception:
                message = exc.detail
            logger_error.error(f"ValidationError: {exc}")
            return Response(
                {
                    "status": False,
                    "message": message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(exc, Exception):
            logger_error.error(f"Exception: {exc}")
            return Response(
                {
                    "status": False,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().handle_exception(exc)
