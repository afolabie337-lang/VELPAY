from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Normalize DRF's default error shapes into one consistent format
        if isinstance(response.data, dict) and 'detail' in response.data:
            response.data = {'error': response.data['detail']}
        elif isinstance(response.data, dict):
            # field validation errors, e.g. {"email": ["This field is required."]}
            first_field = next(iter(response.data))
            first_error = response.data[first_field]
            message = first_error[0] if isinstance(first_error, list) else first_error
            response.data = {'error': f"{first_field}: {message}"}
        return response

    # Unhandled exceptions (bugs) — don't leak Python tracebacks to the client
    return Response(
        {'error': 'Something went wrong. Please try again.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )