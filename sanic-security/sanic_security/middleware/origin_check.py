from urllib.parse import urlparse
from sanic import response


def get_check_origin_func(logger, use_referer_as_fallback: bool,
                          check_origin_against_host: bool,
                          check_origin_against_allowed_origins: bool,
                          allowed_origins: bool):
    """
    Denies access to requests that:
    - dont have the Origin header set
    - have the Origin header, but the value does not match the Host header
    """
    async def check_origin(request):
        """Returns a 403 acces denied  json response
        if the origin is not in the list of allowed origins.
        If there is no origin, referer is used. If both
        headers are not present, access is blocked.
        """

        # TODO make route matching a configurable option
        if not request.path.startswith('/api'):
            return None

        origin = None
        try:
            origin = request.headers['origin']
            logger.debug(f'header origin: {origin}')
        except KeyError:
            pass

        if origin is None and use_referer_as_fallback:
            try:
                origin = request.headers['referer']
                logger.debug(f'header referer: {origin}')
            except KeyError:
                pass

        if origin is None:
            logger.info(f'origin is not set')
            return check_origin.access_denied_response

        parse_result = urlparse(origin)

        # rewriting origin makes it harder to read
        origin_host = parse_result.netloc

        if check_origin_against_host:
            print(request.headers['host'])
            host = request.headers.get('host')
            # TODO: netloc solves origin url to host equivalent, what about referer?
            if host != origin_host:
                logger.info(
                    f'host={host} does not equal origin_host={origin_host} based on origin={origin}'
                )
                # print(f'host: {host}, origin: {origin}, netloc: {res.netloc}')
                return check_origin.access_denied_response

        if check_origin_against_allowed_origins:
            if origin_host not in allowed_origins:
                logger.info(f'origin {origin_host} is not allowed')
                return check_origin.access_denied_response

    check_origin.access_denied_response = response.json(
        {'error': 'access denied'}, status=403)

    return check_origin
