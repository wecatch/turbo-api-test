#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import os.path
import unittest
import inspect
import requests

from turbo_api_test.client import ApiClient
from turbo_api_test.loader import Loader
from turbo_api_test.util import load_yml
from turbo.util import json_decode


TEST_MODULES = [
    'github_test',
]


class Client(ApiClient):
    session  = requests.Session()

    def __init__(self):
        super(Client, self).__init__()
        self.session.headers.update({'agent': 'http://wecatch.me'})

    def decode_response(self, response, **kwargs):
        path_object = kwargs.get('path_object')
        result = json_decode(response.content)
        key = getattr(path_object, 'key', None)
        if key:
            return result[key]
        else:
            return result


def runtest():
    dirname = os.path.dirname(os.path.abspath(__file__))
    modules = [os.path.join(dirname, m) for m in TEST_MODULES]
    for meta in load_yml(os.path.join(dirname, 'main.yml'))['hosts']:
        for path in modules:
            suite = Loader(client=Client).discover(path).loadAllSuite(meta)
            testResult = unittest.TextTestRunner(verbosity=2).run(suite)
            if not testResult.wasSuccessful():
                yield meta, testResult.failures, testResult.errors


def log_error(errors):
    return '\n'.join(['%s %s' % (t._testMethodName, e) for t, e in errors])


def validate(result):
    try:
        if len(result) == 0:
            print 'All hosts api ok'
            sys.exit(0)

        for meta, failures, errors in result:
            print "%s service failures" % meta['host']
            print log_error(failures)
        sys.exit(1)
    except Exception, e:
        print "CRITICAL: Error api check"
        sys.exit(1)


def main():
    validate(list(runtest()))


if __name__ == "__main__":
    main()