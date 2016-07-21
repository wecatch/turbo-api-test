import unittest

from .log import case_log

class ApiTest(unittest.TestCase):

    def is_required(self, meta):
        return meta.get('required', True)

    def assert_data(self, prop, obj):
        for meta in prop['keys']:
            key = meta['name']
            # check is key is required, check key's value type
            if self.is_required(meta):
                self.assertIn(key, obj)
                # self.assert_type(meta, key, obj, prop)
                self.assert_default(meta, key, obj, prop)
            else:
                #if key is not required and key not exist, skip
                if key in obj:
                    self.assert_default(meta, key, obj, prop)

    def assert_default(self, meta, key, obj, prop):
        # not equal default, enter into normal flow
        if 'default' in meta:
            if obj[key] != meta['default']:
                self.assert_type(meta, key, obj, prop)
        else:
            # no default meta, enter into normal flow
            self.assert_type(meta, key, obj, prop)

    def assert_type(self, meta, key, obj, prop):
        ctype = meta['type']
        value = obj[key]

        result = False
        assert_name = ('assert_%s')%ctype
        assert_method = getattr(self, assert_name, None)
        if assert_method:
            result = assert_method(value)
        else:
            raise AssertionError('%s method not found' % assert_name)

        if not result:
            raise AssertionError('assert_type %s:%s:%s:%s is not %s'%(self.__class__.__name__, 
                prop['name'], key, value, ctype))

        if ctype == 'object' and '$ref' in meta:
            obj_name = meta['$ref'].replace('#/definitions/', '')
            self.assert_data(self.definitions[obj_name], value)

    def assert_string(self, value):
        return isinstance(value, basestring)

    def assert_array(self, value):
        return isinstance(value, list)

    def assert_object(self, value):
        return isinstance(value, dict)

    def assert_boolean(self, value):
        return isinstance(value, bool)

    def assert_integer(self, value):
        return isinstance(value, int)

    def assert_long(self, value):
        return isinstance(value, long)

    def assert_float(self, value):
        return isinstance(value, float) or isinstance(value, int)