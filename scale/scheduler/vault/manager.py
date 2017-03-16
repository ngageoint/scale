"""Defines the class that manages caching task secrets to memory"""
from __future__ import unicode_literals

import logging

from vault.exceptions import InvalidSecretsAuthorization, InvalidSecretsRequest, InvalidSecretsToken, InvalidSecretsValue
from vault.secrets_handler import SecretsHandler


logger = logging.getLogger(__name__)


class SecretsManager(object):
    """This class pulls secrets from the secrets backend and caches them. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """
        
        self._all_secrets = {}
    
    def retrieve_job_type_secrets(self, job_name) :
        """Get the secret values from the cache pertaining to the provided job
        
        :param job_name: the name of the job 
        :param type: string
        :return: job type secrets
        :rtype: dict
        """
        
        if job_name in self._all_secrets:
            secret_values = self._all_secrets[job_name]
        else:
            secret_values = {}
            
        return secret_values

    def sync_with_backend(self):
        """Gather all job type secrets that are stored in the secrets backend.
        """

        updated_secrets = {}
        try:
            sh = SecretsHandler()
            jobs_with_secrets = sh.list_job_types()
        except (InvalidSecretsAuthorization, InvalidSecretsRequest, InvalidSecretsToken) as e:
            logger.exception('Secrets Error: %s', e.message)
            return
        
        for job in jobs_with_secrets:
            try:
                job_secrets = sh.get_job_type_secrets(job)
                updated_secrets[job] = job_secrets
            except (InvalidSecretsAuthorization, InvalidSecretsRequest, InvalidSecretsValue) as e:
                logger.exception('Secrets Error: %s', e.message)


secrets_mgr = SecretsManager()
