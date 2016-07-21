# -*- coding: UTF-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

import sys
import os
import re
from fnmatch import fnmatch
import functools
import traceback
import unittest

from .escape import decode_parameters, decode_responses
from .util import load_yml, list_to_dict, assemble_url, import_object
from .case import ApiTest
from .client import ApiClient
from .log import case_log

VALID_MODULE_NAME = re.compile(r'[_a-z]\w*\.py$', re.IGNORECASE)
VALID_YML_NAME = re.compile(r'^(definitions|group)\.yml$', re.IGNORECASE)



def _make_failed_import_test(name):
    message = 'Failed to import test module: %s\n%s' % (name, traceback.format_exc())
    return _make_failed_test('ModuleImportFailure', name, ImportError(message))


def _make_failed_load_tests(name, exception):
    return _make_failed_test('LoadTestsFailure', name, exception)


def _make_failed_test(classname, methodname, exception):
    def testFailure(self):
        raise exception
    attrs = {methodname: testFailure}
    TestClass = type(classname, (ApiTest,), attrs)
    return unittest.suite.TestSuite((TestClass(methodname),))


class RequestObject(object):

    def __init__(self, request_data):
        self.raw = request_data
        self.path, self.query, self.body, self.headers = decode_parameters(request_data.get('parameters', []))
        self.response = {status:dict(decode_responses(value)) for status, value in request_data['responses'].items() if status==200}

    def __str__(self):
        s1 = 'parameters in path: {0}'.format(self.path)
        s2 = 'parameters in query: {0}'.format(self.query)
        s3 = 'parameters in body: {0}'.format(self.body)
        s4 = 'parameters in headers: {0}'.format(self.headers)
        s5 = 'response: {0}'.format(self.response)
        return '\n'.join([s1,s2,s3,s4,s5])

    def __getattr__(self, name):
        if name in self.raw:
            return self.raw[name]
        else:
            raise AttributeError('%s has not attribute %s'%(self, name))

    def __contains__(self, name):
        return name in self.raw


class PathObject(object):

    def __init__(self, path_data):
        self.raw = path_data
        self.path = path_data['path']
        self.name = path_data['name']
        self.request_object = {}
        if 'methods' in path_data:
            self.request_object = {k: RequestObject(v) for k, v in path_data['methods'].items()}

    def __str__(self):
        title = '{name} {path}'.format(name=self.name, path=self.path)
        return '{0}\n{1}'.format(title, ''.join([str(v) for m, v in self.request_object.items()]))

    def __getattr__(self, name):
        if name in self.raw:
            return self.raw[name]
        else:
            raise AttributeError('%s has not attribute %s'%(self, name))

    def __contains__(self, name):
        return name in self.raw


def load_definitions(path):
    return load_yml(path)


def load_main(path):
    return load_yml(path)


def load_group(path):
    data = load_yml(path)
    data['paths'] = list_to_dict(data['paths'], func=lambda x: PathObject(x))
    return data


def create_case_class(name, **attrs):
    return type('%sApiTest'%name.title(), (ApiTest,), dict(attrs))


def create_test_method(name, method, request_object):
    def test_method(self):
        fetch = getattr(self.client, method, None)
        if not method:
            raise AttributeError('%s has no attribute %s'%(self.client, method))

        url = self.url(name)
        try:
            response = fetch(url, params=request_object.query,
                data=request_object.body, headers=request_object.headers)
        except ValueError as e:
            raise AssertionError(e)
        else:
            if response.status_code != 200:
                raise AssertionError('%s request %s'%(url, response.status_code))

            content = self.client.decode_response(response, path_object=self.group['paths'][name], request_object=request_object)
            success = request_object.response[200]
            #type array and not allowEmpty
            if success['type'] == 'array':
                self.assert_array(content)
                if not success['allowEmptyValue']:
                    if success['items_type'] == 'object':
                        self.assert_data(self.definitions[success['items_object']], content[0])
                    else:
                        getattr(self, 'assert_%s'%success['items_type'])(content[0])

            if success['type'] == 'object':
                self.assert_data(self.definitions[success['object']], content)

            if success['type'] not in ['object', 'array']:
                getattr(self, 'assert_%s'%success['type'])(content)

    return test_method


def _url(self, name):
    path_object = self.group['paths'][name]
    return assemble_url(self.host['host'], self.host['basePath'],
        ('%s%s')%(self.group['basePath'], path_object.path), self.group['parameters']['path'])


class Loader(object):

    suiteClass = unittest.suite.TestSuite

    def __init__(self, client=None, definitions=None):
        self.definitions = {}
        self.group = {}
        self.client = ApiClient()
        if definitions:
            self.definitions.update(definitions)

        if client:
            self.client = client

    def loadTestsFromTestCase(self, testCaseClass):
        return unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass)

    def loadTestsFromModule(self, module, use_load_tests=True):
        return unittest.defaultTestLoader.loadTestsFromModule(module, use_load_tests)

    def load_definitions(self, package_dir):
        definitions_path = os.path.join(package_dir, 'definitions.yml')
        if os.path.isfile(definitions_path):
            self.definitions.update(load_definitions(definitions_path))
    
    def load_group(self, package_dir):
        group_path = os.path.join(package_dir, 'group.yml')
        if os.path.isfile(group_path):
            self.group = load_group(group_path)

    def discover(self, start_dir, pattern='*test*.py'):
        package_dir = os.path.abspath(start_dir)
        if not os.path.isfile(os.path.join(package_dir, '__init__.py')):
            raise ValueError('%s is not a valid package'%start_dir)

        parrent_dir = os.path.dirname(package_dir)
        if parrent_dir not in sys.path:
            sys.path.insert(0, parrent_dir)

        self.load_definitions(package_dir)
        self.load_group(package_dir)
        self.find_yml_tests()
        self.find_py_tests(package_dir, pattern)

        return self

    def find_yml_tests(self):
        # add client, definitions, group into caseClass
        self.ymlCaseClass = create_case_class(self.group['group'], client=self.client.create_instance(), group=self.group, definitions=self.definitions)
        for name, path_obj in self.group['paths'].items():
            if 'skip' in path_obj and path_obj.skip:
                continue

            # setup testmethod add request object
            for method, r_obj in path_obj.request_object.items():
                setattr(self.ymlCaseClass, 'test_%s'%('%s_%s'%(name, method)), create_test_method(name, method, r_obj))

        setattr(self.ymlCaseClass, 'url', _url)

    def loadYmlSuite(self, host):
        return self.loadSuite(self.ymlCaseClass, host)

    def find_py_tests(self, package_dir, pattern):
        self.pyCaseClass = []
        for path in os.listdir(package_dir):
            if not VALID_MODULE_NAME.match(path):
                continue

            if not fnmatch(path, pattern):
                continue

            full_path = os.path.join(package_dir, path)
            name, _ = os.path.splitext(path)
            try:
                test_module = '%s.%s'%(os.path.basename(package_dir), name)
                module = import_object(test_module)
            except Exception as e:
                case_log.error(e, exc_info=True)
                self.pyCaseClass.append(_make_failed_import_test(name))
            else:
                self.inject_into_module(module)
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, ApiTest):
                        setattr(obj, 'client', self.client.create_instance())
                        setattr(obj, 'group', self.group)
                        setattr(obj, 'definitions', self.definitions)
                        setattr(obj, 'url', _url)
                        self.pyCaseClass.append(obj)

    @staticmethod
    def inject_host(host, caseClass):
        setattr(caseClass, 'host', host)
        return caseClass

    def loadPySuite(self, host):
        return self.loadSuite(self.pyCaseClass, host)

    def loadAllSuite(self, host):
        case = []
        case.extend(self.pyCaseClass)
        case.append(self.ymlCaseClass)
        return self.loadSuite(case, host)

    def loadSuite(self, case, host):
        if not isinstance(case, list):
            case = [case]
        return self.suiteClass([self.loadTestsFromTestCase(i) for i in map(functools.partial(self.inject_host, host), case)])

    def inject_into_case(self, obj):
        """override it and inject dependence into testcase class
        """
        pass

    def inject_into_module(self, module):
        """override it and inject dependence into module of testcase class
        """
        pass