"""Diagnose provider authentication without displaying key or error message."""
import os
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import ClientError

values = dict(line.split('=', 1) for line in Path('/etc/aio/app.env').read_text().splitlines() if '=' in line)
try:
    with genai.Client(api_key=values['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=15000, retry_options=types.HttpRetryOptions(attempts=1))) as client:
        client.models.get(model=values['GEMINI_MODEL'])
    print('MODEL_ACCESS_OK')
except ClientError as error:
    print('PROVIDER_STATUS=', error.code)
    payload = getattr(error, 'response_json', {}) or {}
    details = payload.get('error', {}).get('details', [])
    import re
    for item in details:
        reason = item.get('reason', '')
        if re.fullmatch('[A-Z_]{1,80}', reason):
            print('PROVIDER_REASON=', reason)
    message = payload.get('error', {}).get('message', '')
    text = message.lower()
    safe_message = str(getattr(error, 'message', '') or message).replace(values['GEMINI_API_KEY'], '[REDACTED]')
    safe_message = re.sub(r'[A-Za-z0-9_.-]{30,}', '[REDACTED]', safe_message)
    print('SANITIZED_PROVIDER_MESSAGE=', safe_message[:700])
    for label, markers in {
        'KEY_INVALID': ('api key not valid', 'invalid api key', 'api key is invalid'),
        'KEY_EXPIRED': ('api key expired', 'expired'),
        'OAUTH_REQUIRED': ('oauth', 'api keys are not supported'),
        'KEY_RESTRICTED': ('restriction', 'blocked', 'not allowed'),
        'MODEL_UNAVAILABLE': ('not found', 'not supported'),
    }.items():
        if any(marker in text for marker in markers):
            print('DIAGNOSIS=', label)
