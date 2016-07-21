from __future__ import absolute_import, division, print_function, with_statement

import re
import os
import sys
import copy
import unittest

import yaml
import requests

from .util import generate_request


class ApiClient(object):

    session = None
    _data = None

    def __init__(self):
        self.method_list = []
        self.setup_method()
        self.setup_request()

    @classmethod
    def create_instance(cls):
        return cls()

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass
    
    def put(self, *args, **kwargs):
        pass

    def head(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def setup_method(self):
        """
        override to add new request method to method_list
        """
        self.method_list = [self.get, self.post, self.put, self.head, self.delete]

    def setup_request(self):
        for i in generate_request(lambda x: x, self.method_list, self.session):
            setattr(self, i.func_name, i)

    def decode_response(self, response, *args, **kwargs):
        """override and decode response content 
        """
        return response.content