# coding=utf-8

from os import environ as ENV
from typing import Optional
import requests
import base64
import logging
from jwt import PyJWT, PyJWKClient, ExpiredSignatureError, InvalidAudienceError
import streamlit as st
from streamlit.legacy_caching import clear_cache

logger = logging.getLogger(__name__)

_jwt: PyJWT = None
_jwks: PyJWKClient = None

@st.cache
def _init() -> None:
  global _jwt, _jwks

  tenant_id = ENV['TENANT_ID']

  url = f'https://us-south.appid.cloud.ibm.com/oauth/v4/{tenant_id}/.well-known/openid-configuration'
  resp = requests.get(url)
  jwks_uri = resp.json()['jwks_uri']

  _jwt = PyJWT()
  _jwks = PyJWKClient(jwks_uri, cache_keys=True, cache_jwk_set=True)

# @st.cache(ttl=3600)
def get_token() -> Optional[str]:
  return st.session_state.get('access_token', None)

def login(
  username: str = '', password: str = '', grant_type: str = 'password'
) -> None:
  tenant_id = ENV['TENANT_ID']
  client_id = ENV['CLIENT_ID']
  client_secret = ENV['CLIENT_SECRET']

  _ = clear_cache()
  username, password = st.session_state['username'], st.session_state['password']

  try:
    url = f'https://us-south.appid.cloud.ibm.com/oauth/v4/{tenant_id}/token'
    b64_encoded_client_credential = base64.b64encode(
      f'{client_id}:{client_secret}'.encode()
    ).decode()
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': f'Basic {b64_encoded_client_credential}'
    }
    resp = requests.post(
      url,
      headers=headers,
      data={
        'grant_type': grant_type,
        'username': username,
        'password': password
      }
    )
    if not resp.ok:
      raise RuntimeError(f'Retrieve Token Failed: {resp.text}')
    access_token = resp.json()['access_token']
  except RuntimeError:
    st.session_state['access_token'] = None
  else:
    st.session_state['access_token'] = access_token
    # don't store username + password
    del st.session_state['password']
    del st.session_state['username']

def verify(token: str, online: bool = False) -> bool:
  tenant_id = ENV['TENANT_ID']
  client_id = ENV['CLIENT_ID']
  client_secret = ENV['CLIENT_SECRET']

  if not token:
    return False

  if online:
    url = f'https://us-south.appid.cloud.ibm.com/oauth/v4/{tenant_id}/introspect'
    b64_encoded_client_credential = base64.b64encode(
      f'{client_id}:{client_secret}'.encode()
    ).decode()
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': f'Basic {b64_encoded_client_credential}'
    }
    resp = requests.post(
      url,
      headers=headers,
      data={
        'token': token
      }
    )
    if not resp.ok:
      raise RuntimeError(f'Verify Token Failed: {resp.text}')
    else:
      successed = resp.json().get('active', False)
  else:
    try:
      public_key = _jwks.get_signing_key_from_jwt(token).key
      _ = _jwt.decode(
        token,
        key=public_key,
        audience=[client_id],
        algorithms=['RS256'],
        options={
          'verify_exp': True,
          'verify_aud': True
        }
      )
      successed = True
    except (ExpiredSignatureError, InvalidAudienceError):
      successed = False
    except BaseException as e:
      raise RuntimeError(f'Retrieve Token Failed: {e}')
  return successed

if __name__ == '__main__':
  from dotenv import load_dotenv
  load_dotenv(override=True)

  _init()

  access_token = login(username='fangwch@IBM', password='fangwch@IBM')
  ok = verify(access_token)
  logger.warning(f'Verify Status: {ok}')
else:
  _init()
