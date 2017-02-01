# -*- coding: utf-8 -*-


# Copyright 2017 Akamai Technologies http://developer.akamai.com.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
import sys; sys.path.append("../akamai/authtoken")
if sys.version_info[0] >= 3:
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

from authtoken import AuthToken

import requests


AT_HOSTNAME = "token-auth.akamaized.net"
import secrets
AT_ENCRYPTION_KEY = secrets.AT_ENCRYPTION_KEY
AT_TRANSITION_KEY = secrets.AT_TRANSITION_KEY
AT_SALT = secrets.AT_SALT
DEFAULT_DURATION = 5 * 1000 # 5s


class TestAuthToken(unittest.TestCase):

    def setUp(self):
        # Test for Query String
        self.at = AuthToken(key=AT_ENCRYPTION_KEY, duration=DEFAULT_DURATION)
        
        # Test for Cookie
        self.cat = AuthToken(key=AT_ENCRYPTION_KEY, algorithm='sha1', duration=DEFAULT_DURATION)

        # Test for Header
        self.hat = AuthToken(key=AT_ENCRYPTION_KEY, algorithm='md5', duration=DEFAULT_DURATION)

    def _token_setting(self, ttype, escape_early, transition):
        t = None
        if ttype == 'q':
            t = self.at
        elif ttype == 'c':
            t = self.cat
        elif ttype == 'h':
            t = self.hat
        
        if transition:
            t.key = AT_TRANSITION_KEY
        else:
            t.key = AT_ENCRYPTION_KEY
        
        t.escape_early = escape_early

    def _queryAssertEqual(self, path, expacted, query='', escape_early=True, transition=False,
                          payload=None, session_id=None):
        self._token_setting('q', escape_early, transition)
        token = self.at.generateToken(url=path, payload=None, session_id=None)
        # print(path)
        url = "http://{0}{1}{4}{2}={3}".format(AT_HOSTNAME, path, token.name, token.token,
            '&' if '?' in path else '?')
        # print(url)
        response = requests.get(url)
        self.assertEqual(expacted, response.status_code)
    
    def _cookieAssertEqual(self, path, expacted, escape_early=True, transition=False,
                           payload=None, session_id=None):
        self._token_setting('c', escape_early, transition)

        token = self.cat.generateToken(url=path, payload=None, session_id=None)
        url = "http://{0}{1}".format(AT_HOSTNAME, path)
        response = requests.get(url, cookies={token.name: token.token})
        self.assertEqual(expacted, response.status_code)

    def _headerAssertEqual(self, path, expacted, escape_early=True, transition=False,
                           payload=None, session_id=None):
        self._token_setting('h', escape_early, transition)

        token = self.hat.generateToken(url=path, payload=None, session_id=None)
        url = "http://{0}{1}".format(AT_HOSTNAME, path)
        response = requests.get(url, headers={token.name: token.token})
        self.assertEqual(expacted, response.status_code)
        
    def _test_case_set(self, query_path, cookie_path, header_path, escape_early):
        # General Test
        self._queryAssertEqual(query_path, 404, escape_early=escape_early)
        self._cookieAssertEqual(cookie_path, 404, escape_early=escape_early)
        self._headerAssertEqual(header_path, 404, escape_early=escape_early)

        # QueryString and EscapeEarly Test
        query_string="?foo=bar&hello=world"
        self._queryAssertEqual(query_path + query_string, 403, escape_early=(False==escape_early))
        self._cookieAssertEqual(cookie_path + query_string, 403, escape_early=(False==escape_early))
        self._headerAssertEqual(header_path + query_string, 403, escape_early=(False==escape_early))
        
        # escape_query_string = quote_plus(query_string)
        # self._queryAssertEqual(query_path + escape_query_string, 404, escape_early=escape_early)
        # self._cookieAssertEqual(cookie_path + escape_query_string, 404, escape_early=escape_early)
        # self._headerAssertEqual(header_path + escape_query_string, 404, escape_early=escape_early)

        # Transition Key Test
        self._queryAssertEqual(query_path, 404, transition=True, escape_early=escape_early)
        self._cookieAssertEqual(cookie_path, 404, transition=True, escape_early=escape_early)
        self._headerAssertEqual(header_path, 404, transition=True, escape_early=escape_early)

        # Payload Test
        self._queryAssertEqual(query_path, 404, payload='SOME_PAYLOAD_DATA', escape_early=escape_early)
        self._cookieAssertEqual(cookie_path, 404, payload='SOME_PAYLOAD_DATA', escape_early=escape_early)
        self._headerAssertEqual(header_path, 404, payload='SOME_PAYLOAD_DATA', escape_early=escape_early)

        # Session Id Test
        self._queryAssertEqual(query_path, 404, session_id='SOME_SESSION_ID_DATA', escape_early=escape_early)
        self._cookieAssertEqual(cookie_path, 404, session_id='SOME_SESSION_ID_DATA', escape_early=escape_early)
        self._headerAssertEqual(header_path, 404, session_id='SOME_SESSION_ID_DATA', escape_early=escape_early)
    
    def test_escape_on_ignoreQuery_yes(self):
        self._test_case_set("/q_escape_ignore", "/c_escape_ignore", "/h_escape_ignore", escape_early=True)

    def test_escape_off_ignoreQuery_yes(self):
        self._test_case_set("/q_ignore", "/c_ignore", "/h_ignore", escape_early=False)

    def test_escape_on_ignoreQuery_no(self):
        query_path = "/q_escape"
        cookie_path = "/c_escape"
        header_path = "/h_escape"
        query_string="?foo=bar&hello=world"

        self._queryAssertEqual(query_path + query_string, 404, escape_early=True)
        self._cookieAssertEqual(cookie_path + query_string, 404, escape_early=True)
        self._headerAssertEqual(header_path + query_string, 404, escape_early=True)

        self._test_case_set(query_path, cookie_path, header_path, escape_early=True)
    
    def test_escape_off_ignoreQuery_no(self):
        query_path = "/q"
        cookie_path = "/c"
        header_path = "/h"
        query_string="?foo=bar&hello=world"
        
        self._queryAssertEqual(query_path + query_string, 404, escape_early=False)
        self._cookieAssertEqual(cookie_path + query_string, 404, escape_early=False)
        self._headerAssertEqual(header_path + query_string, 404, escape_early=False)

        self._test_case_set(query_path, cookie_path, header_path, escape_early=False)
    
    def test_query_escape_on_ignore_yes_with_salt(self):
        query_salt_path = "/salt"
        ats = self.at = AuthToken(key=AT_ENCRYPTION_KEY, salt=AT_SALT, duration=DEFAULT_DURATION)
        token = ats.generateToken(url=query_salt_path)
        url = "http://{0}{1}?{2}={3}".format(AT_HOSTNAME, query_salt_path, token.name, token.token)
        response = requests.get(url)
        self.assertEqual(404, response.status_code)
        

if __name__ == '__main__':
    unittest.main()