"""Request middleware for logging and session management."""

import logging
import time

from flask import Flask, Response, g, request, session

logger = logging.getLogger(__name__)


def register_middleware(app: Flask) -> None:
    """Register before/after request handlers on the app."""

    @app.before_request
    def before_request_logging() -> None:
        """Store request start time for timing calculation."""
        g.start_time = time.perf_counter()

    @app.before_request
    def refresh_session() -> None:
        session.modified = True

    @app.after_request
    def after_request_logging(response: Response) -> Response:
        """Log API requests with timing information."""
        if not request.path.startswith("/api/"):
            return response

        duration_ms = (time.perf_counter() - g.start_time) * 1000
        user_id = session.get("user", {}).get("id", "anonymous")
        status_code = response.status_code
        method = request.method
        path = request.path

        log_msg = (
            f"[API] {method} {path} | User: {user_id} | {duration_ms:.0f}ms | {status_code}"
        )

        if status_code >= 500:
            logger.error(log_msg)
        elif status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return response
