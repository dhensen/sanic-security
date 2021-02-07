import random
import uuid
import logging
from urllib.parse import urlparse

from prometheus_client import Counter
from sanic import Sanic
from sanic.response import json
from sanic_prometheus import monitor

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

exception_counter = Counter('exception_count', 'exception count')


class UserException(Exception):
    pass


app = Sanic(__name__)

# request_id generations decreases bare RPS by factor 4
GENERATE_REQUEST_ID = True
USE_HSTS = True
ORIGIN_CHECK = True
USE_REFERER_AS_FALLBACK = True
CHECK_ORIGIN_AGAINST_HOST = True
CHECK_ORIGIN_AGAINST_ALLOWED_ORIGINS = True
ALLOWED_ORIGINS = [
    '127.0.0.1:8000', 'localhost:8000', 'localhost', 'foobar.com'
]

if USE_HSTS:

    @app.middleware('response')
    async def insert_hsts(request, response):
        response.headers[
            'Strict-Transport-Security'] = 'max-age=86400; includeSubDomains'


if ORIGIN_CHECK:

    @app.middleware('request')
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
            log.debug(f'header origin: {origin}')
        except KeyError:
            pass

        if origin is None and USE_REFERER_AS_FALLBACK:
            try:
                origin = request.headers['referer']
                log.debug(f'header referer: {origin}')
            except KeyError:
                pass

        if origin is None:
            log.info(f'origin is not set')
            return check_origin.access_denied_response

        parse_result = urlparse(origin)

        # rewriting origin makes it harder to read
        origin_host = parse_result.netloc

        if CHECK_ORIGIN_AGAINST_HOST:
            host = request.headers.get('host')
            # TODO: netloc solves origin url to host equivalent, what about referer?
            if host != origin_host:
                log.info(
                    f'host {host} does not equal origin_host={origin_host} based on origin={origin}'
                )
                # print(f'host: {host}, origin: {origin}, netloc: {res.netloc}')
                return check_origin.access_denied_response

        if CHECK_ORIGIN_AGAINST_ALLOWED_ORIGINS:
            if origin_host not in ALLOWED_ORIGINS:
                log.info(f'origin {origin_host} is not allowed')
                return check_origin.access_denied_response

    check_origin.access_denied_response = json({'error': 'access denied'},
                                               status=403)


@app.middleware('request')
async def set_request_id(request):
    request_id = request.headers.get('X-Request-ID')

    if GENERATE_REQUEST_ID and not request_id:
        request_id = str(uuid.uuid4())

    if request_id:
        request.ctx.request_id = request_id

@app.middleware('request')
async def log_request_id(request):
    log.info(f'request_id={request.ctx.request_id}')

@app.middleware('response')
async def set_request_id_response_header(request, response):
    response.headers['X-Request-ID'] = request.ctx.request_id


app.static('/', 'index.html')


@app.route('/api/ip')
async def get_ip(request):
    if random.random() < 0.1:
        raise UserException('random error')

    ip = request.headers.get('x-real-ip') or request.ip
    return json({'data': {'ip': ip}})


@app.exception(Exception)
async def all_exceptions(request, exception):
    exception_counter.inc()
    message = 'server_error'
    if isinstance(exception, UserException):
        message = f'{message}: {exception}'
    return json({'error': {'message': message}}, status=500)


if __name__ == "__main__":
    import os
    extra = {'debug': True}
    if os.getenv('SKIP_LOGGING'):
        print('SKIP_LOGGING env var is set:')
        print(' - disabling debug')
        extra['debug'] = False
        print(' - disabling access_log')
        extra['access_log'] = False

    # option 1 - add /metrics endpoint next to other endpoints
    monitor(app).expose_endpoint()
    extra['workers'] = 4

    # option 2 - run /metrics on a separate port
    # monitor(app).start_server(addr="0.0.0.0", port=8001)
    # this one does not work with multiple workers
    extra['ssl'] = {'cert': "./cert.pem", 'key': "./key.pem"}

    app.run(host="0.0.0.0", port=8443, **extra)
