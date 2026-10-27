"""
Centralized Error Code Registry for SkillBridge.
Provides structured metadata, client-safe explanations, and recovery guidance.
"""

ERROR_REGISTRY = {
    '400': {
        'code': '400',
        'http_status': 400,
        'title': 'Bad Request',
        'meaning': 'The server cannot process the request due to malformed syntax or missing required fields.',
        'typical_cause': 'Invalid payload, missing mandatory fields in JSON, or corrupt multipart upload.',
        'explanation': 'The request was missing required information or had an invalid format.',
        'recovery_action': 'Check your form inputs or upload parameters and try again.',
        'retryable': False,
    },
    '401': {
        'code': '401',
        'http_status': 401,
        'title': 'Unauthorized',
        'meaning': 'Authentication is required and has failed or has not been provided.',
        'typical_cause': 'Missing or expired Bearer / Token authorization header, or session timeout.',
        'explanation': 'You need to be logged in to perform this operation.',
        'recovery_action': 'Log in with your email and password or refresh your session.',
        'retryable': False,
    },
    '403': {
        'code': '403',
        'http_status': 403,
        'title': 'Forbidden',
        'meaning': 'The client does not have permission to access the requested resource.',
        'typical_cause': 'Attempting to view or edit another user’s resume, match analysis, or modifying protected sample jobs.',
        'explanation': 'You do not have permission to access or edit this resource.',
        'recovery_action': 'Ensure you are signed in to the account that owns this resource.',
        'retryable': False,
    },
    '404': {
        'code': '404',
        'http_status': 404,
        'title': 'Not Found',
        'meaning': 'The server cannot find the requested resource or endpoint route.',
        'typical_cause': 'Incorrect URL path, deleted resume or job ID, or non-existent record.',
        'explanation': 'The requested page or resource could not be found.',
        'recovery_action': 'Check the URL or return to the Dashboard.',
        'retryable': False,
    },
    '429': {
        'code': '429',
        'http_status': 429,
        'title': 'Too Many Requests',
        'meaning': 'The user has sent too many requests in a given amount of time.',
        'typical_cause': 'Exceeded rate limit for resume parsing, AI chat, or matching operations.',
        'explanation': 'You have exceeded the request rate limit for this action.',
        'recovery_action': 'Please wait a moment before sending another request.',
        'retryable': True,
    },
    '500': {
        'code': '500',
        'http_status': 500,
        'title': 'Internal Server Error',
        'meaning': 'The server encountered an unexpected condition that prevented it from fulfilling the request.',
        'typical_cause': 'Unhandled exception, database query error, or parsing crash.',
        'explanation': 'An unexpected server error occurred. Our engineering team has been notified.',
        'recovery_action': 'Try again in a few seconds or submit a support ticket if the issue persists.',
        'retryable': True,
    },
    '503': {
        'code': '503',
        'http_status': 503,
        'title': 'Service Unavailable',
        'meaning': 'The server is currently unable to handle the request due to maintenance or upstream dependency failure.',
        'typical_cause': 'Background database maintenance, ML service offline, or network partition.',
        'explanation': 'The service is temporarily unavailable. Upstream services may be restarting.',
        'recovery_action': 'Wait 30 seconds and retry your operation.',
        'retryable': True,
    },
    'SB-1001': {
        'code': 'SB-1001',
        'http_status': 422,
        'title': 'Resume Processing Failed',
        'meaning': 'The document could not be converted or text could not be extracted by the parsing engine.',
        'typical_cause': 'Scanned/image-only PDF without OCR text, password-protected PDF, corrupted DOCX file, or unsupported binary encoding.',
        'explanation': 'We were unable to extract readable text from your uploaded resume.',
        'recovery_action': 'Ensure the file is a text-selectable PDF or DOCX file under 10MB and does not require a password.',
        'retryable': False,
    },
}

def get_error_info(code_or_status: str | int) -> dict:
    key = str(code_or_status).strip().upper()
    if key in ERROR_REGISTRY:
        return ERROR_REGISTRY[key]
    # Check if key matches an http_status
    for item in ERROR_REGISTRY.values():
        if str(item['http_status']) == key:
            return item
    return {
        'code': key,
        'http_status': 500,
        'title': 'Unknown Error',
        'meaning': 'An uncataloged error occurred.',
        'explanation': 'An unexpected condition was reported.',
        'recovery_action': 'Contact support if this error continues.',
        'retryable': False,
    }
