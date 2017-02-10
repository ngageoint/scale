"""Handles secret getters and setters for Scale"""

import requests
import jwt
import json

from django.conf import settings
from vault.exceptions import InvalidSecretsBackend, InvalidSecretsAuthorization, InvalidSecretPath, InvalidSecretsRequest


class SecretsHandler(object):
    """Represents a secrets handler for setting and retrieving secrets
    """

    def __init__(self):
        """Creates a secrets handler object.  The backend is initially tested to ensure it exists and Scale can
        authenticate properly with it.
        """
        
        self.vault_error_codes = {
            200: 'Status Code 200- Success with data.',
            204: 'Status Code 204- Success, no data returned.',
            400: 'Status Code 400- Invalid request, missing or invalid data. See the "validation" section for more details on the error response.',
            403: 'Status Code 403- Forbidden, your authentication details are either incorrect or you dont have access to this feature.',
            404: 'Status Code 404- Invalid path. This can both mean that the path truly doesnt exist or that you dont have permission to view a specific path. We use 404 in some cases to avoid state leakage.',
            429: 'Status Code 429- Rate limit exceeded. Try again after waiting some period of time.',
            500: 'Status Code 500- Internal server error. An internal error has occurred, try again later. If the error persists, report a bug.',
            503: 'Status Code 503- Vault is down for maintenance or is currently sealed. Try again later.',
        }
        
        self.secrets_url = settings.VAULT_URL
        self.secrets_token = settings.VAULT_TOKEN
        self.service_account = settings.VAULT_SERVICE_ACCOUNT

        if self.service_account:
            self.dcos_token = self._dcos_authenticate()
        else: 
            self.dcos_token = None
            self._vault_authenticate()
            
        self._check_secrets_backend()
        
    def get_job_type_secret(self, secret_path, secret_name):
        """Retrieves the value pertaining to the secret_name provided, located at the secret_path

        :param secret_path: path within the secrets backend that the secret is stored
        :type secret_path: str
        :param secret_name: name of the secret being requested
        :type secret_name: str
        :return: secret_value
        :rtype: str
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
            url = ''.join([url, 'secret/default/scale/job-type', secret_path, '/', secret_name])
            get_secret = requests.request(method='GET',
                                          url=url,
                                          headers={'Content-Type': 'application/json'},
                                          data=json.dumps({'uid': self.service_account, 'token': self.dcos_token}))
            # Status == [403: forbidden][404: secret not found][200: Proper return]
            
            if get_secret.status_code == 200:
                response = get_secret.json()
                secret_value = response['value']
            elif get_secret.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif get_secret.status_code == 404:
                raise InvalidSecretPath('No secret was found at ' + url)
        else: 
            url = url + 'secret/scale/job-type' + secret_path
            get_secret = requests.request(method='GET',
                                          url=url,
                                          headers={'Content-Type': 'application/json', 
                                                   'X-Vault-Token': self.secrets_token})
            
            if get_secret.status_code == 200:
                response = get_secret.json()
                secret_value = response['data'][secret_name]
            elif get_secret.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            else:
                raise InvalidSecretsRequest('Expected status code 200 from ' + url + ' - Received: ' +
                                            self.vault_error_codes[get_secret.status_code])

        return secret_value
        
    def set_job_type_secret(self, secret_path, secret_value, secret_name):
        """write a job-type secret to the secrets backend

        :param secret_path: path within the secrets backend that the secret will be stored.
        :type secret_path: str
        :param secret_value: secret value to be stored
        :type secret_value: str
        :param secret_name: name to associate with the stored value
        :type secret_name: str
        :return:
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
            create_secret_data = {
                'uid': self.service_account,
                'token': self.dcos_token,
                'author': 'scale',
                'value': secret_value
            }
            
            url = ''.join([url, 'secret/default/scale/job-type', secret_path, '/', secret_name])
            set_secret = requests.request(method='PUT',
                                          url=url,
                                          headers={'Content-Type': 'application/json'},
                                          data=json.dumps(create_secret_data))
            # Status == [403: forbidden][201: Proper return]
            
            if set_secret.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif set_secret.status_code != 201:
                raise InvalidSecretsRequest('Expected status code 201 from ' + url + ' - Received: ' +
                                            set_secret.status_code)
        else: 
            create_secret_data = {
                secret_name: secret_value
            }
            
            url = url + 'secret/scale/job-type' + secret_path
            set_secret = requests.request(method='POST',
                                          url=url,
                                          headers={'Content-Type': 'application/json', 
                                                   'X-Vault-Token': self.secrets_token},
                                          data=json.dumps(create_secret_data))
            
            if set_secret.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif set_secret.status_code != 204:
                raise InvalidSecretsRequest('Expected status code 204 from ' + url + ' - Received: ' +
                                            self.vault_error_codes[set_secret.status_code])
    
    def _check_secrets_backend(self):
        """Validates that Scale can transact with the secrets backend properly.
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
            # Logging - Check if DCOS secrets store exists
            url += '/store/scale'
            check_mount = requests.request(method='GET',
                                           url=url,
                                           headers={'Content-Type': 'application/json'},
                                           data=json.dumps({'uid': self.service_account, 'token': self.dcos_token}))
            
            # Status == [403: forbidden][404: backend not found][200: backend exists]
            
            if check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif check_mount.status_code == 404:
                self._create_dcos_store()
           
        else:
            # Logging - Check if vault secrets store exists
            url += '/sys/mounts'
            check_mount = requests.request(method='GET',
                                           url=url,
                                           headers ={"Content-Type": "application/json",
                                                     "X-Vault-Token": self.secrets_token})
            # Status == [403: forbidden][404: backend not found][200: Proper request]
            
            if check_mount.status_code == 200:
                if 'scale/' not in json.loads(check_mount.content).keys():
                    self._create_vault_store()
            elif check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif check_mount.status_code == 404:
                self._create_dcos_store()
            
    def _create_dcos_store(self):
        """Create a new store within the DC/OS Vault backend that will be used for all Scale secrets.

        **As of 9FEB2017 DC/OS does not support additional backends.**
        """
        
        # Logging - attempting to create DCOS:vault backend for scale
        
        create_store_data = {
            'uid': self.service_account,
            'token': self.dcos_token,
            'name': 'Scale Secrets Store',
            'description': 'Secrets store for all secrets used by Scale',
            'driver': 'vault',
            'initialized': True,
            'sealed': False
        }
        
        url = self.secrets_url + '/store/scale'
        create_mount = requests.request(method='PUT',
                                        url=url,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(create_store_data))
        # Status == [201: Store successfully created][409: Already exists][403: Forbidden]
        
        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
        elif create_mount.status_code not in [201, 409]:
            raise InvalidSecretsRequest('Got HTTP status code ' + create_mount.status_code +
                                        ' (expected 201 or 409) from ' + url)
    
    def _create_vault_store(self):
        """Create a new store within the Vault backend that will be used for all Scale secrets.
        """
        
        # Logging - attempting to create vault backend for scale

        create_store_json = {
            'type': 'generic',
            'description': 'Secrets store for all secrets used by Scale'
        }
        
        url = self.secrets_url + '/sys/mounts/scale'
        create_mount = requests.request(method='POST',
                                        url=url,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(create_store_json))
        # Status == [204: Store successfully created][403: Forbidden][400: Already exists]
        
        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
        elif create_mount.status_code not in [200, 400]:
            raise InvalidSecretsRequest('Expected status code 200 or 400 from ' + url + ' - Received: ' +
                                        self.vault_error_codes[create_mount.status_code])
    
    def _dcos_authenticate(self):
        """Authenticate with DC/OS Vault backend and expect a status code 200 returned.
        """
        
        token = jwt.encode({'uid': self.service_account}, self.secrets_token, algorithm='RS256')

        url = self.secrets_url + '/acs/api/v1/auth/login'
        request_auth = requests.request(method='POST',
                                        url=url,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps({'uid': self.service_account, 'token':token}))
        
        if request_auth.status_code != 200:
            raise UnreachableSecretsBackend('Got HTTP status code ' + request_auth.status_code +
                                            ' (expected 200) from ' + url)
        
        self.secrets_url += '/secrets/v1'
        access_token = [k + '=' + v for k, v in request_auth.json().items()]

        return access_token
        
    def _vault_authenticate(self):
        """Authenticate with Vault and expect a status code 200 returned.
        """
        
        url = self.secrets_url + '/v1/sys/health'
        check_status = requests.request(method='GET',
                                        url=url,
                                        headers={'Content-Type': 'application/json'})
        
        if check_status.status_code != 200:
            raise InvalidSecretsRequest('Expected status code 200 from ' + url + ' - Received: ' +
                                        self.vault_error_codes[check_status.status_code])
        
        self.secrets_url += '/v1'
