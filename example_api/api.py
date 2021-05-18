import random
import uuid
import logging

from prometheus_client import Counter
from sanic import Sanic
from sanic.response import json
from sanic_prometheus import monitor
from sanic_security import SanicSecurity

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

exception_counter = Counter('exception_count', 'exception count')


class UserException(Exception):
    pass


app = Sanic(__name__)
SanicSecurity(app,
              allowed_origins=[
                  '127.0.0.1:8443', 'localhost:8443', '127.0.0.1:8000',
                  'localhost:8000', 'localhost', 'foobar.com'
              ])

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
        logger.debug('SKIP_LOGGING env var is set:')
        logger.debug(' - disabling debug')
        logger.debug(' - disabling access_log')
        extra['debug'] = False
        extra['access_log'] = False

    # option 1 - add /metrics endpoint next to other endpoints
    # monitor(app).expose_endpoint()
    extra['workers'] = 4

    # option 2 - run /metrics on a separate port
    # monitor(app).start_server(addr="0.0.0.0", port=8001)
    # this one does not work with multiple workers
    extra['ssl'] = {'cert': "./cert.pem", 'key': "./key.pem"}

    app.run(host="0.0.0.0", port=8443, **extra)
