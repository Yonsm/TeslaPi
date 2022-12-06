import uuid
import json
import base64
import time
import os
import hashlib
from httpx import Client
from urllib.parse import quote

import logging
LOGGER = logging.getLogger(__package__)

TESLAPI_TOKEN = 'teslapi.token'


class TeslaPi(Client):
    access_token = None

    def __init__(self, email, password):
        super().__init__(http2=True, verify=False)
        try:
            with open(TESLAPI_TOKEN) as f:
                token = json.load(f)
            if time.time() + 10 * 60 > token[1]:
                LOGGER.info('Refresh token...')
                token = self.oauth_token(token[2])
        except:
            LOGGER.info('Authorizing...')
            try:
                token = self.authorize(email, password)
            except:
                LOGGER.error('Login failed')
                self.access_token = None
                return
        self.access_token = token[0]

    def app_headers(self, need_key=True):
        headers = {
            'content-type': 'application/json',
            'x-tesla-app-key': '029260B036CADB983512CC669A64111F95631EBF' if need_key else '',
            'user-agent': 'Tesla/4.14.4 (com.teslamotors.TeslaApp; build:1455; iOS 16.1.2) Alamofire/5.2.1',
            'x-tesla-user-agent': 'TeslaApp/4.14.4-1455/6a4c86898a/ios/16.1.2',
            "x-txid": str(uuid.uuid1()).upper(),
        }
        if self.access_token:
            headers['authorization'] = 'Bearer ' + self.access_token
        return headers

    def authorize(self, email, password):
        code_verifier = base64.urlsafe_b64encode(os.urandom(32))
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b'=').decode()
        state = quote(base64.b64encode(os.urandom(32)).decode())
        url = f'https://auth.tesla.cn/oauth2/v3/authorize?audience=&client_id=ownerapi&code_challenge={code_challenge}&code_challenge_method=S256&locale=zh-CN&prompt=login&redirect_uri=https%3A%2F%2Fauth.tesla.com%2Fvoid%2Fcallback&response_type=code&scope=openid%20email%20offline_access&state={state}'
        headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
        res = self.get(url, headers=headers)
        text = res.text
        form = text.find('sso-form sign-in-form')
        values = {}
        for name in ['_csrf', 'transaction_id']:
            tag = text.find(name, form)
            value = text.find('value="', tag) + 7
            end = text.find('"', value)
            values[name] = text[value:end]
        _csrf = values['_csrf']
        transaction_id = values['transaction_id']
        email = self.email.replace('@', '%40')
        data = f'_csrf={_csrf}&_phase=authenticate&_process=1&cancel=&transaction_id={transaction_id}&change_identity=&identity={email}&credential={password}'
        headers['content-type'] = 'application/x-www-form-urlencoded'
        res = self.post(url, data=data, headers=headers)
        text = res.text
        pos = text.find('code=') + 5
        end = text.find('&', pos)
        code = text[pos:end]

        return self.oauth_token(code=code, code_verifier=code_verifier.decode())

    def oauth_token(self, refresh_token=None, code=None, code_verifier=None):
        data = {
            'scope': 'openid email offline_access',
            'client_id': 'ownerapi',
        }
        if refresh_token:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = refresh_token
        else:
            data['grant_type'] = 'authorization_code'
            data['redirect_uri'] = 'https://auth.tesla.com/void/callback'
            data['code'] = code
            data['code_verifier'] = code_verifier

        res = self.post('https://auth.tesla.cn/oauth2/v3/token', json=data, headers=self.app_headers(need_key=refresh_token))
        r = res.json()
        expires_in = r['expires_in'] + int(time.time())
        token = [r['access_token'], expires_in, r['refresh_token']]
        with open(TESLAPI_TOKEN, 'w') as f:
            json.dump(token, f)
        return token

    def products(self):
        res = self.get('https://owner-api.vn.cloud.tesla.cn/api/1/products?orders=1', headers=self.app_headers())
        return res.json().get('response')

    def vehicle_data(self, vid):
        url = f'https://owner-api.vn.cloud.tesla.cn/api/1/vehicles/{vid}/vehicle_data?endpoints=charge_state%3Bclimate_state%3Bclosures_state%3Bdrive_state%3Bgui_settings%3Blocation_state%3Bvehicle_config%3Bvehicle_state%3Bvehicle_data_combo'
        res = self.get(url, headers=self.app_headers())
        return res.json()['response']
