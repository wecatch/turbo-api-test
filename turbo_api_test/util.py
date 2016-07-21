from __future__ import absolute_import, division, print_function, with_statement

import re
import functools
import sys
import os.path
import unittest

import yaml
import requests


def import_object(name, package_space=None):
    if name.count('.') == 0:
        return __import__(name, package_space, None)

    parts = name.split('.')
    obj = __import__('.'.join(parts[:-1]), package_space, None, [str(parts[-1])], 0)
    try:
        return getattr(obj, parts[-1])
    except AttributeError:
        raise ImportError("No module named %s" % parts[-1])


def assemble_request(decode_response, session=None):
    def wrapper_outer(func):
        @functools.wraps(func)
        def wrapper_inner(*args, **kwargs):
            if not session:
                response = getattr(requests, func.func_name)(*args, **kwargs)
            else:
                response = getattr(session, func.func_name)(*args, **kwargs)

            return decode_response(response)

        return wrapper_inner

    return wrapper_outer


def assemble_url(host, base_path, path, path_param=None):
    if not path_param:
        path_param = {}

    pattern = re.compile(r'\{\w*\}')
    new_path = path
    for group in pattern.findall(path):
        key = group[1:-1]
        if key not in path_param:
            raise ValueError('path parameter %s not found'%key)

        new_path = new_path.replace('{%s}'%key, str(path_param[key]))

    return '{host}{base_path}{path}'.format(host=host, base_path=base_path, path=new_path)


def generate_request(decode_response, funclist, session=None):
    return [assemble_request(decode_response, session)(i) for i in funclist]


def load_yml(full_path):
    if not os.path.isfile(full_path):
        raise ValueError('%s is not file'%full_path)

    with open(full_path) as f:
        return yaml.load(f.read())


def list_to_dict(data, key='name', func=lambda x: x):
    return {g[key]:func(g) for g in data}