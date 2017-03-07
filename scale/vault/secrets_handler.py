"""Handles secret getters and setters for Scale"""

import ast
import jwt
import json
import requests

from django.conf import settings
from vault.exceptions import InvalidSecretsAuthorization, InvalidSecretsRequest, InvalidSecretsToken, InvalidSecretsValue


class SecretsHandler(object):
    """Represents a secrets handler for setting and retrieving secrets
    """

    def __init__(self):
        """Creates a secrets handler object.  The backend is initially tested to ensure it exists and Scale can
        authenticate properly with it.
        """

        self.secrets_error_codes = {
            400: 'Status Code 400 - Invalid request, missing or invalid data.',
            403: 'Status Code 403 - Forbidden, authentication details are incorrect or no access to feature.',
            404: 'Status Code 404 - Invalid path, secret or backend not found.',
            409: 'Status Code 409 - Secret or secret store already exists.',
            429: 'Status Code 429 - Rate limit exceeded.',
            500: 'Status Code 500 - Internal server error.',
            503: 'Status Code 503 - Secrets store is down for maintenance or is currently sealed.',
        }

        self.secrets_url = settings.SECRETS_URL
        self.secrets_token = settings.SECRETS_TOKEN
        self.service_account = settings.DCOS_SERVICE_ACCOUNT

        if self.service_account:
            self.dcos_token = self._dcos_authenticate()
        else:
            self.dcos_token = None
            self._vault_authenticate()

        self._check_secrets_backend()

    def get_job_type_secrets(self, job_name):
        """Retrieves the secrets located at the job_name within the backend

        :param job_name: path within the secrets backend that the secret is stored
        :type job_name: str
        :return: secret_values
        :rtype: str
        """

        url = self.secrets_url

        if self.dcos_token:
            url = ''.join([url, 'secret/default/scale/job-type/', job_name])
            data = json.dumps({'uid': self.service_account, 'token': self.dcos_token})
            get_secret = self._make_request('GET', url, data=data)
            
            try:
                response = get_secret.json()
                secret_values = ast.literal_eval(response['value'])
            except SyntaxError:
                raise InvalidSecretsValue('The DCOS secrets value could not be converted to JSON.')
        
        else:
            url = url + 'secret/scale/job-type/' + job_name
            headers = {
                'Content-Type': 'application/json',
                'X-Vault-Token': self.secrets_token
            }
            get_secret = self._make_request('GET', url, headers=headers)
            
            response = get_secret.json()
            secret_values = response['data']

        return secret_values

    def list_job_types(self):
        """Gets the names of all job types that have secrets 

        :return: all_job_types
        :rtype: list
        """

        url = self.secrets_url

        if self.dcos_token:
            url += 'secret/default/scale/job-type?list=true'
            data = json.dumps({'uid': self.service_account, 'token': self.dcos_token})
            list_jobs = self._make_request('GET', url, data=data)
            
            response = list_jobs.json()
            all_job_types = response['array']

        else:
            url += 'secret/scale/job-type'
            headers = {
                'Content-Type': 'application/json',
                'X-Vault-Token': self.secrets_token
            }
            list_jobs = self._make_request('LIST', url, headers)

            response = list_jobs.json()
            all_job_types = response['data']['keys']

        return all_job_types

    def set_job_type_secrets(self, secret_path, secret_json):
        """write job-type secrets to the secrets backend

        :param secret_path: path within the secrets backend that the secret will be stored.
        :type secret_path: str
        :param secret_json: dict with name:value pairs for all secrets associated with the job
        :type secret_json: dict
        :return:
        """

        url = self.secrets_url
        secret_values = json.dumps(secret_json)

        if self.dcos_token:
            url = ''.join([url, 'secret/default/scale/job-type', secret_path])
            data = json.dumps({
                'uid': self.service_account,
                'token': self.dcos_token,
                'author': 'scale',
                'value': secret_values
            })
            set_secret = self._make_request('PUT', url, data=data)

        else:
            url = ''.join([url, 'secret/scale/job-type', secret_path])
            headers = {
                'Content-Type': 'application/json',
                'X-Vault-Token': self.secrets_token
            }
            data = secret_values
            set_secret = self._make_request('PUT', url, headers, data)

    def _check_secrets_backend(self):
        """Validates that Scale can transact with the secrets backend properly.
        """

        url = self.secrets_url

        if self.dcos_token:
            url += '/store/scale'
            data = json.dumps({
                'uid': self.service_account, 'token': self.dcos_token
            })

            check_mount = self._make_request('GET', url, data=data, catch_error=False)

            if check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when getting a secret')
            elif check_mount.status_code == 404:
                self._create_dcos_store()

        else:
            url += '/sys/mounts'
            headers = {
                "Content-Type": "application/json",
                "X-Vault-Token": self.secrets_token
            }

            check_mount = self._make_request('GET', url, headers=headers, catch_error=False)

            if check_mount.status_code == 200:
                if 'scale/' not in json.loads(check_mount.content).keys():
                    self._create_vault_store()
            elif check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when getting a secret')
            elif check_mount.status_code == 404:
                self._create_dcos_store()

    def _create_dcos_store(self):
        """Create a new store within the DC/OS Vault backend that will be used for all Scale secrets.

        **As of 9FEB2017 DC/OS does not support additional backends.**
        """

        url = self.secrets_url + '/store/scale'
        data = json.dumps({
            'uid': self.service_account,
            'token': self.dcos_token,
            'name': 'Scale Secrets Store',
            'description': 'Secrets store for all secrets used by Scale',
            'driver': 'vault',
            'initialized': True,
            'sealed': False
        })
        create_mount = self._make_request('GET', url, data=data, catch_error=False)

        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when getting a secret')
        elif create_mount.status_code not in [201, 409]:
            raise InvalidSecretsRequest('Invalid request return: ' + self.secrets_error_codes[r.status_code])

    def _create_vault_store(self):
        """Create a new store within the Vault backend that will be used for all Scale secrets.
        """

        url = self.secrets_url + '/sys/mounts/scale'
        data = json.dumps({
            'type': 'generic',
            'description': 'Secrets store for all secrets used by Scale'
        })
        create_mount = self._make_request('GET', url, data=data)

        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when getting a secret')
        elif create_mount.status_code not in [200, 400]:
            raise InvalidSecretsRequest('Invalid request return: ' + self.secrets_error_codes[r.status_code])

    def _dcos_authenticate(self):
        """Authenticate with DC/OS Vault backend and expect a status code 200 returned.
        """

        try:
            token = jwt.encode({'uid': self.service_account}, self.secrets_token, algorithm='RS256')
        except ValueError:
            raise InvalidSecretsToken('The provided token could not be encoded: ')

        url = self.secrets_url + '/acs/api/v1/auth/login'
        data = json.dumps({
            'uid': self.service_account, 'token':token
        })

        request_auth = self._make_request('GET', url, data=data)

        self.secrets_url += '/secrets/v1/'
        access_token = [k + '=' + v for k, v in request_auth.json().items()]
        
        return access_token

    def _make_request(self, method, url, headers=None, data=None, catch_error=True):
        """Make a request to the secrets backend with the provided variables

        :param method: string that determines GET or POST request type
        :type method: str
        :param url: string containing the url for the request
        :type url: str
        :param headers: headers to attach to the request
        :type headers: json
        :param data: data to attach to the request
        :type data: json
        :param data: flag to catch error before return
        :type data: bool

        :return: an object containing information from the request
        :rtype: requests.request
        """

        if not headers:
            headers = {
                'Content-Type': 'application/json'
            }

        if not data:
            data = {}

        r = requests.request(method=method, url=url, headers=headers, data=data)
        
        if catch_error and r.status_code in self.secrets_error_codes:
            if r.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when getting a secret')
            else:
                raise InvalidSecretsRequest('Invalid request return: ' + self.secrets_error_codes[r.status_code])
        
        return r

    def _vault_authenticate(self):
        """Authenticate with Vault and expect a status code 200 returned.
        """

        url = self.secrets_url + '/v1/sys/health'
        request_auth = self._make_request('GET', url)
        self.secrets_url += '/v1/'
