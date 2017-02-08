"""Handles secret getters and setters for Scale"""

import requests
import jwt
import json

from django.conf import settings
from vault.exceptions import UnreachableSecretsBackend, InvalidSecretsAuthorization



class SecretsHandler(object):
    """
    """

    def __init__(self):
        """
        """
        
        self.secrets_url = settings.VAULT_URL
        self.secrets_token = settings.VAULT_TOKEN

        if settings.VAULT_SERVICE_ACCOUNT:
            self.dcos_token = self._dcos_authenticate(settings.VAULT_SERVICE_ACCOUNT, self.secrets_token)
        else: 
            self.dcos_token = None
            self._vault_authenticate()
            
        self._check_secrets_backend()
        
    def _check_secrets_backend(self):
        
        url = self.secrets_url
        
        if self.dcos_token:
           # Logging - Check if DCOS secrets store exists
        
            check_mount = requests.request(method='GET',
                                           url=url + '/store/scale',
                                           headers={'Content-Type': 'application/json'},
                                           data=json.dumps({'uid':service_account, 'token':token}))
            
            # Status == [403: forbidden][404: backend not found][200: backend exists]
            if check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif check_mount.status_code == 404:
                self._create_dcos_store()
           
        else:
            # Logging - Check if vault secrets store exists
            
            check_mount = requests.request(method ='GET',
                                           url = url + '/sys/mounts',
                                           headers = {"Content-Type": "application/json",
                                                      "X-Vault-Token": self.secrets_token})
            
            # Status == [403: forbidden][404: backend not found][200: Proper request]
            if 'scale/' not in json.loads(check_mount.content).keys():
                self._create_vault_store()
            
            
            if check_mount.status_code == 403:
                raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
            elif check_mount.status_code == 404:
                self._create_dcos_store()
            
    def _create_dcos_store(self):
        
        url = self.secrets_url
        
        # Logging - attempting to create DCOS:vault backend for scale
        
        create_store_json = {
            'uid': service_account, 
            'token': self.dcos_token,
            'name': 'Scale Secrets Store',
            'description': 'Secrets store for all secrets used by Scale',
            'driver': 'vault',
            'initialized': true,
            'sealed': false
        }
        
        create_mount = requests.request(method='PUT',
                                        url=url + '/store/scale',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(create_store_json))
        
        # Status == [201: Store successfully created][409: Already exists][403: Forbidden]
        
        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
    
    def _create_vault_store(self):
        
        url = self.secrets_url
        
        # Logging - attempting to create vault backend for scale
        
        create_store_json = {
            'type': 'generic',
            'description': 'Secrets store for all secrets used by Scale'
        }
        
        create_mount = requests.request(method='POST',
                                        url=url + '/sys/mounts/scale',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(create_store_json))
        
        # Status == [204: Store successfully created][403: Forbidden][400: Already exists]
        
        if create_mount.status_code == 403:
            raise InvalidSecretsAuthorization('Permission was denied when accessing ' + url)
    
    def _dcos_authenticate(self):
        """
        """
        
        url = self.secrets_url + '/acs/api/v1/auth/login'
        token = jwt.encode({'uid': self.VAULT_SERVICE_ACCOUNT}, self.VAULT_TOKEN, algorithm='RS256')

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
        
        url = self.secrets_url + '/v1/sys/health'
        
        check_status = requests.request(method='GET',
                                        url=url,
                                        headers={'Content-Type': 'application/json'})
        
        if check_status.status_code != 200:
            raise UnreachableSecretsBackend('Got HTTP status code '+check_status.status_code+' (expected 200) from '+url)
        
        self.secrets_url = self.secrets_url + '/v1'
