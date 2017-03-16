from __future__ import unicode_literals


import json
import requests
from mock import patch, MagicMock

import django
from django.conf import settings
from django.test import TestCase, TransactionTestCase

from error.models import Error
from vault.secrets_handler import SecretsHandler
from vault.exceptions import InvalidSecretsAuthorization, InvalidSecretsRequest, InvalidSecretsToken


class SecretsBackendValidation(TestCase):
    """Tests performing requests to the secrets backend"""
    
    def setUp(self):
        
        self.dcos_token = \
"""
-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgFoDzg4Q8Jmzw0s1FcMM8BhKlWwcpO2GjkL7g1mGsVEbqaWyz1G3
TaV7bHvBb/D4ceN8AV8CBzaNVidNGaIZNoeTiPNmQ6PfnuXBJLaFMfQjGxeyxxf5
eOoP8U7ukRCEa6YHn41TlWzYKW1Nc5gpzdO47o8aaMkF0D3grDOp4G3BAgMBAAEC
gYBR70CyYQ0AezZ60Jk8cBxjoBAe1nvxkRcRNWs8JHRmha2IHBjGIvnUdWIry8mf
KCZSkN+WoXv7Ve9j2rRIbnbJHzEZTXcyxRuA+YRxkGYtCWSzMvw3csuvUG4lpCOg
hQL4dZHfuWIrrNVteN7UEvN+0dlMotQH9XO/bhn+zoIxGQJBAKvVF6j1SRxj3ucv
e6LsLywo6pQIjz+yKZ0ngFJe+FNLISXKspK/tym1IWMD3SZy6tf7mdx2oXnsyy85
1w9PwJ8CQQCGGzXs5382a2YzxWkSsq3niEmQn61NJbHMCOzE2w2fqt4xV2Ka/lp5
3NEg6Q2mRrTpmZvRI3fQtPN4dY8pvVWfAkBdpZvobA21WESSEFG8YCXxVjdKCEQx
vaJqUK3htnp1wptFImwiCDQFmf6hHOj43GZa4XdgLJMihMfTbB1l7dwXAkAVOMsg
0UWFVBuZR70n81Sn1h5mH46qLbPkKOlnAY83XC/LORvmkSe6LyJ9BcReMsRAT0mk
H+u/AFOjFV9xaH/bAkEAgRi3VkUQNAdsEGVzHHq93s5CSZLz2gHoyTMCZu/G31pF
UB3V/SWf7Wqp9vDEbUtgzIn9y4l5cIjS/J2IKkYARg==
-----END RSA PRIVATE KEY-----
"""

        django.setup()
        
    def mocked_validate(*args):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
    
            def json(self):
                return self.json_data
                
            def content(self):
                return self.json_data
    
        if not args: 
            return MockResponse({}, 403)
        
        elif args[0] == 'vault':
            r_return = MagicMock()
            r_return.status_code = 200
            r_return.content = json.dumps({
                "scale/": {
                    "config": {
                        "default_lease_ttl": 0,
                        "max_lease_ttl": 0
                    },
                    "description": "scale secrets storage",
                    "type": "generic",
                }
            })
            
            return r_return
        
        elif args[0] == 'dcos':
            status_code = 200
            content = {
                "token": "some_good_token"
            }
            return MockResponse(content, status_code)
        
        return MockResponse({}, 404)

    @patch('requests.request', return_value=mocked_validate('dcos'))    
    def test_dcos_authenticate_good_return(self, mock_request):
        with self.settings(SECRETS_TOKEN=self.dcos_token,
                          DCOS_SERVICE_ACCOUNT='some_account_name',
                          SECRETS_URL='HTTP://127.0.0.1:8200'):
            auth_test = SecretsHandler()

    @patch('requests.request', return_value=mocked_validate('dcos'))    
    def test_dcos_authenticate_bad_token(self, mock_request):
        with self.settings(SECRETS_TOKEN='some_bad_token',
                          DCOS_SERVICE_ACCOUNT='some_account_name',
                          SECRETS_URL='HTTP://127.0.0.1:8200'):
            self.assertRaises(InvalidSecretsToken, SecretsHandler)

    @patch('requests.request', return_value=mocked_validate('vault'))    
    def test_vault_authenticate_good_return(self, mock_request):
        with self.settings(SECRETS_TOKEN='some_master_token',
                          DCOS_SERVICE_ACCOUNT=None,
                          SECRETS_URL='HTTP://127.0.0.1:8200'):
            auth_test = SecretsHandler()

    @patch('requests.request', return_value=mocked_validate())    
    def test_vault_authenticate_bad_permission(self, mock_request):
        with self.settings(SECRETS_TOKEN='some_master_token',
                          DCOS_SERVICE_ACCOUNT=None,
                          SECRETS_URL='HTTP://127.0.0.1:8200'):
            self.assertRaises(InvalidSecretsAuthorization, SecretsHandler)
            
            
class VaultSecretsValueValidation(TestCase):
    """Tests setting and recieving secrets"""
    
    def setUp(self):
        self.secret_test_path = 'job_name-0.0.0'
        
        self.vault_setup()
        django.setup()

    def mocked_get_secret(*args):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
    
            def json(self):
                return self.json_data
                
            def content(self):
                return self.json_data
    
        if not args: 
            return MockResponse({}, 403)
        
        elif args[0] == 'secret':
            status_code = 200
            content = {
                "request_id": "some_id",
                "lease_id": "",
                "lease_duration": 0,
                "renewable": "false",
                "data": {
                    "test_val_name": "vault_backend_secret",
                    "foo": "bar"
                },
                "warnings": "null"
            }
            
            return MockResponse(content, status_code)
        
        return MockResponse({}, 404)

    def mocked_request_setup():
        r_return = MagicMock()
        r_return.status_code = 200
        r_return.content = json.dumps({
            "scale/": {
                "config": {
                    "default_lease_ttl": 0,
                    "max_lease_ttl": 0
                },
                "description": "scale secrets storage",
                "type": "generic",
            }
        })
        
        return r_return

    @patch('requests.request', return_value=mocked_request_setup())    
    def vault_setup(self, mock_request):
        with self.settings(SECRETS_TOKEN='some_master_token',
                          DCOS_SERVICE_ACCOUNT=None,
                          SECRETS_URL='HTTP://127.0.0.1:8200'):

            self.vault_backend = SecretsHandler()

    @patch('requests.request', return_value=mocked_get_secret('secret'))    
    def test_vault_get_secret(self, mock_request):
        test_secret = self.vault_backend.get_job_type_secrets(self.secret_test_path)
        self.assertEqual(test_secret, {"test_val_name": "vault_backend_secret", "foo": "bar"})

    @patch('requests.request', return_value=mocked_get_secret())    
    def test_vault_get_bad_secret(self, mock_request):
        self.assertRaises(InvalidSecretsAuthorization, 
                          self.vault_backend.get_job_type_secrets, 
                          self.secret_test_path)


class DCOSSecretsValueValidation(TestCase):
    """Tests setting and recieving secrets"""
    
    def setUp(self):
        
        self.dcos_token = \
"""
-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgFoDzg4Q8Jmzw0s1FcMM8BhKlWwcpO2GjkL7g1mGsVEbqaWyz1G3
TaV7bHvBb/D4ceN8AV8CBzaNVidNGaIZNoeTiPNmQ6PfnuXBJLaFMfQjGxeyxxf5
eOoP8U7ukRCEa6YHn41TlWzYKW1Nc5gpzdO47o8aaMkF0D3grDOp4G3BAgMBAAEC
gYBR70CyYQ0AezZ60Jk8cBxjoBAe1nvxkRcRNWs8JHRmha2IHBjGIvnUdWIry8mf
KCZSkN+WoXv7Ve9j2rRIbnbJHzEZTXcyxRuA+YRxkGYtCWSzMvw3csuvUG4lpCOg
hQL4dZHfuWIrrNVteN7UEvN+0dlMotQH9XO/bhn+zoIxGQJBAKvVF6j1SRxj3ucv
e6LsLywo6pQIjz+yKZ0ngFJe+FNLISXKspK/tym1IWMD3SZy6tf7mdx2oXnsyy85
1w9PwJ8CQQCGGzXs5382a2YzxWkSsq3niEmQn61NJbHMCOzE2w2fqt4xV2Ka/lp5
3NEg6Q2mRrTpmZvRI3fQtPN4dY8pvVWfAkBdpZvobA21WESSEFG8YCXxVjdKCEQx
vaJqUK3htnp1wptFImwiCDQFmf6hHOj43GZa4XdgLJMihMfTbB1l7dwXAkAVOMsg
0UWFVBuZR70n81Sn1h5mH46qLbPkKOlnAY83XC/LORvmkSe6LyJ9BcReMsRAT0mk
H+u/AFOjFV9xaH/bAkEAgRi3VkUQNAdsEGVzHHq93s5CSZLz2gHoyTMCZu/G31pF
UB3V/SWf7Wqp9vDEbUtgzIn9y4l5cIjS/J2IKkYARg==
-----END RSA PRIVATE KEY-----
"""

        self.secret_test_path = 'job_name-0.0.0'

        self.dcos_setup()
        django.setup()
        
    def mocked_get_secret(*args):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
    
            def json(self):
                return self.json_data
                
            def content(self):
                return self.json_data
    
        if not args: 
            return MockResponse({}, 403)

        elif args[0] == 'secret':
            status_code = 200
            content = {
                "value": "{'some_name': 'some_secret'}"
                }
            return MockResponse(content, status_code)
            
        elif args[0] == 'auth':
            status_code = 200
            content = {
                "value": "dcos_token"
                }
            return MockResponse(content, status_code)
    
        
        return MockResponse({}, 404)
        
    def mocked_request_setup():
        r_return = MagicMock()
        r_return.status_code = 200
        r_return.content = {
            'dcos_token': 'foobar'
        }
        
        return r_return
            
    @patch('requests.request', return_value=mocked_get_secret('auth'))    
    def dcos_setup(self, mock_request):
        with self.settings(SECRETS_TOKEN=self.dcos_token,
                          DCOS_SERVICE_ACCOUNT='some_account_name',
                          SECRETS_URL='HTTP://127.0.0.1:8200'):
            self.dcos_backend = SecretsHandler()
        
    @patch('requests.request', return_value=mocked_get_secret('secret'))    
    def test_dcos_get_secret(self, mock_request):
            test_secret = self.dcos_backend.get_job_type_secrets(self.secret_test_path)
            self.assertEqual(test_secret, {'some_name': 'some_secret'})
    
    #@patch('vault.secrets_handler.SecretsHandler._make_request', return_value=mocked_get_secret())  
    @patch('requests.request', return_value=mocked_get_secret())  
    def test_dcos_get_bad_secret(self, mock_request):
            secret_name = 'test_val_name'
            self.assertRaises(InvalidSecretsAuthorization, 
                              self.dcos_backend.get_job_type_secrets,
                              self.secret_test_path)
