from turbo_api_test.client import ApiClient
from turbo_api_test.loader import Loader
import unittest

def main():
    from turbo.util import json_decode
    class Client(ApiClient):
        def decode_response(self, response, **kwargs):
            path_object = kwargs.get('path_object')
            result = json_decode(response.content)['res']
            return result[path_object.key]

    path = '/home/zhyq/adesk/api-test/example/hello_test'
    host = {'host': 'http://service.picasso.adesk.com', 'basePath': ''}
    loader = Loader(client=Client).discover(path)
    testResult = unittest.TextTestRunner(verbosity=2).run(loader.loadAllSuite(host))
    for testCase, result in testResult.failures:
        print(testCase)
    
      
if __name__ == '__main__':
    main()