import time
import uuid
import logging

logger = logging.getLogger('skillbridge.requests')

class RequestCorrelationAndLoggingMiddleware:
    """
    Attaches a unique X-Request-ID to every request/response and logs execution timing.
    Filters sensitive query parameters from log output.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtain or generate request correlation ID
        request_id = request.headers.get('X-Request-ID') or f"req_{uuid.uuid4().hex[:12]}"
        request.request_id = request_id

        start_time = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        response['X-Request-ID'] = request_id

        # Clean query path (omit sensitive tokens if any)
        clean_path = request.path
        if request.META.get('QUERY_STRING'):
            clean_query = "&".join(
                param for param in request.META['QUERY_STRING'].split('&')
                if not any(secret in param.lower() for secret in ['token', 'password', 'key', 'secret'])
            )
            if clean_query:
                clean_path = f"{clean_path}?{clean_query}"

        status_code = getattr(response, 'status_code', 500)
        logger.info(
            f"[{request_id}] {request.method} {clean_path} -> {status_code} ({duration_ms}ms)"
        )

        return response
