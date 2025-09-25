"""
Standardized API response system for consistent formatting
"""
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from django.core.paginator import Paginator, Page
from django.db.models import QuerySet
from rest_framework.pagination import PageNumberPagination
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class StandardizedResponse:
    """Class for creating standardized API responses"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Request successful",
        meta: Optional[Dict] = None,
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        Create a standardized success response

        Args:
            data: Response data
            message: Success message
            meta: Additional metadata
            status_code: HTTP status code

        Returns:
            Response object with standardized format
        """
        response_data = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }

        if meta:
            response_data['meta'] = meta

        return Response(response_data, status=status_code)

    @staticmethod
    def error(
        error: str,
        details: Optional[Dict] = None,
        error_code: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> Response:
        """
        Create a standardized error response

        Args:
            error: Error message
            details: Additional error details
            error_code: Application-specific error code
            status_code: HTTP status code

        Returns:
            Response object with standardized error format
        """
        response_data = {
            'success': False,
            'error': error,
            'timestamp': timezone.now().isoformat()
        }

        if details:
            response_data['details'] = details

        if error_code:
            response_data['error_code'] = error_code

        # Log error for monitoring
        logger.error(f"API Error: {error} (Code: {error_code}) - Details: {details}")

        return Response(response_data, status=status_code)

    @staticmethod
    def validation_error(
        validation_errors: Dict[str, List[str]],
        message: str = "Validation failed"
    ) -> Response:
        """
        Create a standardized validation error response

        Args:
            validation_errors: Dictionary of field validation errors
            message: Error message

        Returns:
            Response object with validation error format
        """
        response_data = {
            'success': False,
            'error': message,
            'validation_errors': validation_errors,
            'timestamp': timezone.now().isoformat()
        }

        logger.warning(f"Validation Error: {validation_errors}")

        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def not_found(
        resource: str = "Resource",
        resource_id: Optional[str] = None
    ) -> Response:
        """
        Create a standardized not found response

        Args:
            resource: Resource type that was not found
            resource_id: ID of the resource that was not found

        Returns:
            Response object with not found format
        """
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"

        return StandardizedResponse.error(
            error=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def unauthorized(
        message: str = "Authentication required"
    ) -> Response:
        """
        Create a standardized unauthorized response

        Args:
            message: Authentication error message

        Returns:
            Response object with unauthorized format
        """
        return StandardizedResponse.error(
            error=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def forbidden(
        message: str = "Permission denied"
    ) -> Response:
        """
        Create a standardized forbidden response

        Args:
            message: Permission error message

        Returns:
            Response object with forbidden format
        """
        return StandardizedResponse.error(
            error=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def rate_limit_exceeded(
        retry_after: Optional[int] = None,
        message: str = "Rate limit exceeded"
    ) -> Response:
        """
        Create a standardized rate limit response

        Args:
            retry_after: Seconds until retry is allowed
            message: Rate limit message

        Returns:
            Response object with rate limit format
        """
        details = {}
        if retry_after:
            details['retry_after'] = retry_after

        response = StandardizedResponse.error(
            error=message,
            details=details,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

        if retry_after:
            response['Retry-After'] = str(retry_after)

        return response

    @staticmethod
    def server_error(
        message: str = "Internal server error",
        error_id: Optional[str] = None
    ) -> Response:
        """
        Create a standardized server error response

        Args:
            message: Error message
            error_id: Unique error identifier for tracking

        Returns:
            Response object with server error format
        """
        details = {}
        if error_id:
            details['error_id'] = error_id

        logger.error(f"Server Error: {message} (ID: {error_id})")

        return StandardizedResponse.error(
            error=message,
            details=details,
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class EnhancedPageNumberPagination(PageNumberPagination):
    """Enhanced pagination with standardized response format"""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return paginated response in standardized format"""
        return StandardizedResponse.success(
            data=data,
            message="Data retrieved successfully",
            meta={
                'pagination': {
                    'page': self.page.number,
                    'pages': self.page.paginator.num_pages,
                    'page_size': self.page_size,
                    'count': self.page.paginator.count,
                    'has_next': self.page.has_next(),
                    'has_previous': self.page.has_previous(),
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                }
            }
        )


def paginate_queryset(
    queryset: QuerySet,
    page_number: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Helper function to paginate a queryset

    Args:
        queryset: Django QuerySet to paginate
        page_number: Page number to retrieve
        page_size: Number of items per page

    Returns:
        Dictionary with paginated data and metadata
    """
    paginator = Paginator(queryset, page_size)

    try:
        page = paginator.page(page_number)
    except Exception:
        page = paginator.page(1)

    return {
        'data': list(page.object_list.values()) if hasattr(page.object_list, 'values') else list(page.object_list),
        'pagination': {
            'page': page.number,
            'pages': paginator.num_pages,
            'page_size': page_size,
            'count': paginator.count,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
        }
    }


class ResponseHelper:
    """Helper class with common response patterns"""

    @staticmethod
    def created(data: Any, message: str = "Resource created successfully") -> Response:
        """Standard response for resource creation"""
        return StandardizedResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )

    @staticmethod
    def updated(data: Any, message: str = "Resource updated successfully") -> Response:
        """Standard response for resource updates"""
        return StandardizedResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_200_OK
        )

    @staticmethod
    def deleted(message: str = "Resource deleted successfully") -> Response:
        """Standard response for resource deletion"""
        return StandardizedResponse.success(
            data=None,
            message=message,
            status_code=status.HTTP_200_OK
        )

    @staticmethod
    def no_content(message: str = "Request processed successfully") -> Response:
        """Standard response for successful operations with no content"""
        return StandardizedResponse.success(
            data=None,
            message=message,
            status_code=status.HTTP_204_NO_CONTENT
        )

    @staticmethod
    def conflict(
        message: str = "Resource conflict",
        details: Optional[Dict] = None
    ) -> Response:
        """Standard response for resource conflicts"""
        return StandardizedResponse.error(
            error=message,
            details=details,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT
        )

    @staticmethod
    def bad_request(
        message: str = "Bad request",
        details: Optional[Dict] = None
    ) -> Response:
        """Standard response for bad requests"""
        return StandardizedResponse.error(
            error=message,
            details=details,
            error_code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def method_not_allowed(
        allowed_methods: List[str],
        message: str = "Method not allowed"
    ) -> Response:
        """Standard response for method not allowed"""
        return StandardizedResponse.error(
            error=message,
            details={'allowed_methods': allowed_methods},
            error_code="METHOD_NOT_ALLOWED",
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @staticmethod
    def quota_exceeded(
        current_usage: int,
        quota_limit: int,
        message: str = "API quota exceeded"
    ) -> Response:
        """Standard response for quota exceeded"""
        return StandardizedResponse.error(
            error=message,
            details={
                'current_usage': current_usage,
                'quota_limit': quota_limit,
                'usage_percentage': round((current_usage / quota_limit) * 100, 2)
            },
            error_code="QUOTA_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    @staticmethod
    def maintenance_mode(
        message: str = "System under maintenance",
        estimated_downtime: Optional[int] = None
    ) -> Response:
        """Standard response for maintenance mode"""
        details = {}
        if estimated_downtime:
            details['estimated_downtime_minutes'] = estimated_downtime

        return StandardizedResponse.error(
            error=message,
            details=details,
            error_code="MAINTENANCE_MODE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# Common response messages
class Messages:
    """Common response messages for consistency"""

    # Success messages
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    RETRIEVED = "Data retrieved successfully"
    PROCESSED = "Request processed successfully"

    # Error messages
    NOT_FOUND = "Resource not found"
    UNAUTHORIZED = "Authentication required"
    FORBIDDEN = "Permission denied"
    VALIDATION_FAILED = "Validation failed"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
    QUOTA_EXCEEDED = "API quota exceeded"
    INTERNAL_ERROR = "Internal server error"
    BAD_REQUEST = "Bad request"
    CONFLICT = "Resource conflict"
    METHOD_NOT_ALLOWED = "Method not allowed"
    MAINTENANCE_MODE = "System under maintenance"


# Error codes for consistent error handling
class ErrorCodes:
    """Standard error codes for API responses"""

    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"