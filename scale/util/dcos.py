from time import time
from datetime import timedelta

import jwt
import requests

from util.exceptions import ServiceAccountAuthFailure


def generate_token(uid, private_key, scheme='RS256', expiry_seconds=180):
    expire_time = time() + float(timedelta(seconds=expiry_seconds).seconds)
    token = jwt.encode({'exp':expire_time, 'uid': uid}, private_key, algorithm=scheme)
    return token

def dcos_login(secret, verify=False):
    """Take a DCOS service account secret and generate an authentication token

    Input secret must be a dict including uid, private_key, scheme and login_endpoint keys
    """
    user = secret['uid']
    login_token = generate_token(user, secret['private_key'], secret['scheme'])

    payload = {'uid': user, 'token': login_token}
    response = requests.post(secret['login_endpoint'], json=payload, verify=verify)

    if response.status_code == 200:
        return (user, response.json()['token'])

    raise ServiceAccountAuthFailure('Unable to authenticate against DCOS ACS: {} {}'.format(response.status_code,
                                                                                            response.text))