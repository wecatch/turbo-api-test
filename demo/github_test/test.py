from turbo_api_test.case import ApiTest

class GithubApiTest(ApiTest):

    def test_user(self):
        response = self.client.get(self.url('user'))
        content = self.client.decode_response(response,  path_object = self.group['paths']['user'])
        self.assert_data(self.definitions['user'], content)
