from django.test import TestCase
from ...utilities import replace_url_parameter

class ReplaceUrlParameterTest(TestCase):
    '''Tests the replace_url_parameter utility'''

    def test_replace_url_parameter(self):
        url_with_singe_parameter = 'http://example.com/?foo=bar'
        self.assertEqual(replace_url_parameter(url_with_singe_parameter, 'foo', 'baz'), 'http://example.com/?foo=baz')

        url_with_multiple_parameters = 'http://example.com/?foo=bar&baz=qux'
        self.assertEqual(replace_url_parameter(url_with_multiple_parameters, 'foo', 'baz'), 'http://example.com/?foo=baz&baz=qux')

        url_with_multiple_parameters_and_fragment = 'http://example.com/?foo=bar&baz=qux#fragment'
        self.assertEqual(replace_url_parameter(url_with_multiple_parameters_and_fragment, 'foo', 'baz'), 'http://example.com/?foo=baz&baz=qux#fragment')
