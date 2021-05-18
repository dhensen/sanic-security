import uuid


def get_set_request_id_func(generate_request_id):
    async def set_request_id(request):
        # request middleware
        request_id = request.headers.get('X-Request-ID')

        if generate_request_id and not request_id:
            request_id = str(uuid.uuid4())

        if request_id:
            request.ctx.request_id = request_id

    return set_request_id


def get_log_request_id_func(logger):
    async def log_request_id(request):
        # request middleware
        logger.info(f'request_id={request.ctx.request_id}')

    return log_request_id


async def set_request_id_response_header(request, response):
    # response middleware
    try:
        response.headers['X-Request-ID'] = request.ctx.request_id
    except AttributeError:
        pass
