async def add_strict_transport_security_header(request, response):
    # response middleware
    response.headers[
        'Strict-Transport-Security'] = 'max-age=86400; includeSubDomains'
