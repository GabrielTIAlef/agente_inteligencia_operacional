"""Controles de acesso e auditoria para a demonstração local."""

import logging
import os
from collections import deque
from contextvars import ContextVar
from time import monotonic
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")
LOCAL_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
MAX_CHAT_BYTES = 8192
trace_id = ContextVar("trace_id", default="-")


def allowed_origins():
    configured = os.getenv("APP_CORS_ORIGINS")
    if configured is None:
        return list(LOCAL_ORIGINS)
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("APP_CORS_ORIGINS exige origens explícitas.")
    return origins


def local_access(origins):
    """Cria um limitador por processo para a única estação da demo."""
    recent_chat = deque()

    async def audit_and_protect(request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started = monotonic()
        response = None
        if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            response = JSONResponse({"detail": "Acesso restrito à máquina local."}, 403)
        elif request.headers.get("origin") not in (None, *origins):
            response = JSONResponse({"detail": "Origem não autorizada."}, 403)
        elif request.method == "POST" and request.url.path == "/agent/chat":
            response = await protect_chat(request, recent_chat, started)

        if response is None:
            token = trace_id.set(request_id)
            try:
                response = await call_next(request)
            finally:
                trace_id.reset(token)

        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        route = request.scope.get("route")
        logger.info(
            "request_id=%s method=%s route=%s status=%d duration_ms=%.1f",
            request_id, request.method, getattr(route, "path", "unmatched"),
            response.status_code, (monotonic() - started) * 1000,
        )
        return response

    return audit_and_protect


async def protect_chat(request, recent_chat, now):
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        return JSONResponse({"detail": "Envie application/json."}, 415)

    while recent_chat and now - recent_chat[0] >= 60:
        recent_chat.popleft()
    if len(recent_chat) >= 12:
        return JSONResponse({"detail": "Limite local do chat atingido."}, 429, {"Retry-After": "60"})
    recent_chat.append(now)

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_CHAT_BYTES:
            return JSONResponse({"detail": "Corpo da requisição muito grande."}, 413)
        body.extend(chunk)

    # O middleware Starlette reutiliza o corpo em cache ao encaminhar a requisição.
    request._body = bytes(body)
    return None
