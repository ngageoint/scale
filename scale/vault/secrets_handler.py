"""Handles secret getters and setters for Scale"""

import requests
import jwt
import json

from django.conf import settings
from vault.exceptions import UnreachableSecretsBackend, InvalidSecretsAuthorization, InvalidSecretPath, InvalidSecretsRequest



class SecretsHandler(object):
    """
    """

    def __init__(self):
        """
        """
        
        vault_error_codes = {
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

        if settings.VAULT_SERVICE_ACCOUNT:
            self.dcos_token = self._dcos_authenticate(settings.VAULT_SERVICE_ACCOUNT, self.secrets_token)
        else: 
            self.dcos_token = None
            self._vault_authenticate()
            
        self._check_secrets_backend()
        
    def get_job_type_secret(self, secret_path):
        """
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
            url = ''.join([url, 'secret/default/scale/job-type', secret_path, '/', secret_name])
            get_secret = requests.request(method='GET',
                                          url=url,
                                          headers={'Content-Type': 'application/json'},
                                          data=json.dumps({'uid':service_account, 'token':token}))
            # Status == [403: forbidden][404: secret not found][200: Proper return]
            
            if get_secret.status_code == 200:
                response = get_secret.json()
                secret = response['value']
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
                secret = response['data'][secret_name]
            elif get_secret.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            else:
                raise InvalidSecretsRequest('Expected status code 200 from ' + url + ' - Recieved: ' + 
                                            self.vault_error_codes[get_secret.status_code])

        return secret_value
        
    def set_job_type_secret(self, secret_path, secret_value, secret_name):
        """
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
            create_secret_data = {
                'uid': service_account, 
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
                raise InvalidSecretsRequest('Expected status code 201 from ' + url + ' - Recieved: ' + 
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
                raise InvalidSecretsRequest('Expected status code 204 from ' + url + ' - Recieved: ' + 
                                            self.vault_error_codes[set_secret.status_code])
    
    def _check_secrets_backend(self):
        """
        """
        
        url = self.secrets_url
        
        if self.dcos_token:
           # Logging - Check if DCOS secrets store exists
            url = url + '/store/scale
            check_mount = requests.request(method='GET',
                                           url=url,
                                           headers={'Content-Type': 'application/json'},
                                           data=json.dumps({'uid':service_account, 'token':token}))
            
            # Status == [403: forbidden][404: backend not found][200: backend exists]
            
            if check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif check_mount.status_code == 404:
                self._create_dcos_store()
           
        else:
            # Logging - Check if vault secrets store exists
            
            url = url + '/sys/mounts'
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
        """
        """
        
        # Logging - attempting to create DCOS:vault backend for scale
        
        create_store_data = {
            'uid': service_account, 
            'token': self.dcos_token,
            'name': 'Scale Secrets Store',
            'description': 'Secrets store for all secrets used by Scale',
            'driver': 'vault',
            'initialized': true,
            'sealed': false
        }
        
        url = self.secrets_url + '/store/scale'
        create_mount = requests.request(method='PUT',
                                        url=url,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(create_store_data))
        # Status == [201: Store successfully created][409: Already exists][403: Forbidden]
        
        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
    
    def _create_vault_store(self):
        """
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
    
    def _dcos_authenticate(self):
        """
        """
        
        token = jwt.encode({'uid': self.VAULT_SERVICE_ACCOUNT}, self.VAULT_TOKEN, algorithm='RS256')

        url = self.secrets_url + '/acs/api/v1/auth/login'
        request_auth = requests.request(method='POST',
                                        url=url,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps({'uid':self.VAULT_SERVICE_ACCOUNT, 'token':token}))
        
        if request_auth.status_code != 200:
            raise UnreachableSecretsBackend('Got HTTP status code '+request_auth.status_code+' (expected 200) from '+url)
        
        self.secrets_url = self.secrets_url + '/secrets/v1'
        access_token = [k + '=' + v for k, v in request_auth.json().items()]

        return access_token
        
    def _vault_authenticate(self):
        """
        """
        
        url = self.secrets_url + '/v1/sys/health'
        check_status = requests.request(method='GET',
                                        url=url,
                                        headers={'Content-Type': 'application/json'})
        
        if check_status.status_code != 200:
            raise InvalidSecretsRequest('Expected status code 200 from ' + url + ' - Recieved: ' + 
                                        self.vault_error_codes[check_status.status_code])
        
        self.secrets_url = self.secrets_url + '/v1'
