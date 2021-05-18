import logging
from typing import List, Optional

from .middleware.origin_check import get_check_origin_func
from .middleware.request_id import get_set_request_id_func, get_log_request_id_func, set_request_id_response_header
from .middleware.hsts import add_strict_transport_security_header

logger = logging.getLogger(__name__)


class SanicSecurity:
    def __init__(self,
                 app,
                 origin_check: bool = True,
                 use_referer_as_fallback: bool = True,
                 check_origin_against_host: bool = True,
                 check_origin_against_allowed_origins: bool = True,
                 allowed_origins: Optional[List[str]] = None,
                 generate_request_id: bool = True) -> None:
        self._app = app
        self.use_referer_as_fallback = use_referer_as_fallback
        self.check_origin_against_host = check_origin_against_host
        self.check_origin_against_allowed_origins = check_origin_against_allowed_origins
        self.allowed_origins = allowed_origins if allowed_origins else []
        self.generate_request_id = generate_request_id

        if origin_check:
            self.register_origin_check_middleware(self._app)

        self.register_request_id_helper_middleware(self._app)

        app.middleware('response')(add_strict_transport_security_header)

    def register_origin_check_middleware(self, app):
        app.middleware('request')(get_check_origin_func(
            logger, self.use_referer_as_fallback,
            self.check_origin_against_host,
            self.check_origin_against_allowed_origins, self.allowed_origins))

    def register_request_id_helper_middleware(self, app):
        app.middleware('request')(get_set_request_id_func(
            self.generate_request_id))
        app.middleware('request')(get_log_request_id_func(logger))
        app.middleware('response')(set_request_id_response_header)
