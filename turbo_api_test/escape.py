from .util import list_to_dict


def decode_parameters(data):
    """
    :code-block
        'parameters': [{
            'required': False,
            'name': 'skip',
            'allowEmptyValue': True,
            'in': 'query',
            'enum': [0, 1],
            'type': 'integer',
            'description': 'offset'
        }]
    """
    query, body, header, path = {}, {}, {}, {}
    params = list_to_dict(data)
    for k, v in params.items():
        value = parameter_value(v)
        if v['in'] == 'query':
            query[k] = value

        if v['in'] == 'header':
            header[k] = value

        if v['in'] == 'body':
            body[k] = value

        if v['in'] == 'path':
            path[k] = value

    return path, query, body, header


def parameter_value(v):
    if v['type'] in set(['integer', 'float', 'string']):
        if 'enum' in v:
            return v['enum'][0]

    if v['type'] in set(['array']):
        if 'enum' in 'v':
            return v['enum']

    return None


def decode_responses(response):
    """
    :code-block
        'responses': {
            'items': {
                'type': 'object',
                '$ref': '#/definitions/wallpaper'
            },
            'required': True,
            'type': 'array',
            'allowEmptyValue': False
        },
    """
    success = {'type': None, 'default': None, 
        'items_type': None, 'items_object': None, 'allowEmptyValue': None, 'object': None}

    success['type'] = response['type']
    success['allowEmptyValue'] = response['allowEmptyValue']
    if response['type'] == 'array':
        success['items_type'] = response['items']['type']
        #array content object refer
        if '$ref' in response['items']:
            success['items_object'] = response['items']['$ref'].replace('#/definitions/', '')
    
    if response['type'] == 'object':
        #current object refer
        if '$ref' in response:
            success['object'] = response['$ref'].replace('#/definitions/', '')
            
    success['default'] = response.get('default')
    return success