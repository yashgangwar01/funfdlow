import os
import hmac
import hashlib
import json
import logging
import requests
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class SetuAPIError(Exception):
    def __init__(self, message, response_body=None, status_code=None):
        super().__init__(message)
        self.message = message
        self.response_body = response_body
        self.status_code = status_code

    def __str__(self):
        return f"SetuAPIError: {self.message} (Status: {self.status_code}, Body: {self.response_body})"


class SetuAAClient:
    """
    Wrapper around Setu's official Account Aggregator (AA) Gateway v2 REST API.
    Ref: Setu AA OpenAPI Specification (fiu-sandbox.setu.co / orgservice-prod.setu.co)
    """

    def __init__(self):
        self.base_url = os.getenv('SETU_SANDBOX_BASE_URL', 'https://fiu-sandbox.setu.co').rstrip('/')
        self.auth_url = os.getenv('SETU_AUTH_URL', 'https://orgservice-prod.setu.co/v1/users/login')
        self.client_id = os.getenv('SETU_CLIENT_ID', '')
        self.client_secret = os.getenv('SETU_CLIENT_SECRET', '')
        self.product_instance_id = os.getenv('SETU_PRODUCT_INSTANCE_ID', '')
        self.secret_key = os.getenv('SETU_SECRET_KEY', '')

        self._cached_access_token = None

    def _get_access_token(self, force_refresh=False):
        """
        Obtains Bearer access token from Setu's Auth service (https://orgservice-prod.setu.co/v1/users/login).
        Raises SetuAPIError if authentication fails — NO fake fallback tokens are generated.
        """
        if self._cached_access_token and not force_refresh:
            return self._cached_access_token

        if not self.client_id or not self.client_secret:
            raise SetuAPIError("Missing SETU_CLIENT_ID or SETU_CLIENT_SECRET environment variables.")

        headers = {
            'client': 'bridge',
            'Content-Type': 'application/json'
        }
        payload = {
            'clientID': self.client_id,
            'grant_type': 'client_credentials',
            'secret': self.client_secret
        }

        try:
            res = requests.post(self.auth_url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                token = data.get('access_token') or data.get('data', {}).get('access_token')
                if token:
                    self._cached_access_token = token
                    return token
                err_msg = f"Setu auth login returned 200 but missing access_token in response: {res.text}"
                logger.error(err_msg)
                raise SetuAPIError(err_msg, response_body=res.text, status_code=200)
            else:
                err_msg = f"Setu auth login failed ({res.status_code}): {res.text}"
                logger.error(err_msg)
                raise SetuAPIError(err_msg, response_body=res.text, status_code=res.status_code)
        except requests.RequestException as e:
            err_msg = f"Setu auth login network error: {e}"
            logger.error(err_msg)
            raise SetuAPIError(err_msg)

    def _get_headers(self):
        token = self._get_access_token()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'x-product-instance-id': self.product_instance_id
        }

    def _request_with_retry(self, method, url, **kwargs):
        """
        Sends HTTP request with automatic token refresh on HTTP 401.
        Raises SetuAPIError immediately if the request fails after retry.
        """
        headers = self._get_headers()
        kwargs['headers'] = {**headers, **kwargs.get('headers', {})}

        try:
            res = requests.request(method, url, timeout=kwargs.pop('timeout', 15), **kwargs)
            if res.status_code == 401:
                logger.warning("Setu API returned 401 Unauthorized. Retrying with fresh access token...")
                self._get_access_token(force_refresh=True)
                kwargs['headers']['Authorization'] = f'Bearer {self._cached_access_token}'
                res = requests.request(method, url, timeout=15, **kwargs)

            if not (200 <= res.status_code < 300):
                err_msg = f"Setu API request failed ({method} {url}) - Status {res.status_code}: {res.text}"
                logger.error(err_msg)
                raise SetuAPIError(err_msg, response_body=res.text, status_code=res.status_code)

            return res
        except requests.RequestException as e:
            err_msg = f"Network error in Setu API request ({method} {url}): {e}"
            logger.error(err_msg)
            raise SetuAPIError(err_msg)

    def list_fips(self, aa=None, status=None):
        """
        GET /v2/fips — list available FIPs (banks).
        """
        url = f"{self.base_url}/v2/fips"
        params = {}
        if aa:
            params['aa'] = aa
        if status:
            params['status'] = status

        res = self._request_with_retry('GET', url, params=params)
        return res.json()

    def create_consent_request(self, user, vua, date_range_start=None, date_range_end=None):
        """
        POST /v2/consents — creates a consent request.
        `vua` (Virtual User Address) must be provided by the caller in the format
        "{phone_number}@{aa_handle}" e.g. "9999999999@onemoney".
        Raises SetuAPIError immediately on failure. NO mock/fake handles are returned.
        """
        if not vua or '@' not in vua:
            raise SetuAPIError(f"Invalid or missing vua '{vua}'. Expected format: phone@aa_handle")

        now = timezone.now().date()
        start = date_range_start or (now - timedelta(days=90))
        end = date_range_end or now

        payload = {
            "vua": vua,
            "consentDuration": {"unit": "MONTH", "value": 6},
            "consentMode": "STORE",
            "consentTypes": ["TRANSACTIONS", "PROFILE", "SUMMARY"],
            "dataLife": {"unit": "MONTH", "value": 12},
            "fetchType": "PERIODIC",
            # Setu v2 uses "dataRange" with full ISO 8601 datetime strings
            "dataRange": {
                "from": start.strftime('%Y-%m-%dT00:00:00.000Z'),
                "to": end.strftime('%Y-%m-%dT23:59:59.999Z')
            },
            "fiTypes": ["DEPOSIT"],
            "frequency": {"unit": "MONTH", "value": 1},
            "purpose": {
                "code": "101",
                "refUri": "https://api.rebit.org.in/aa/purpose/101.xml",
                "text": "Personal finance management and automated budget allocation",
                "category": {"type": "Personal Finance"}
            },
            "redirectUrl": "http://127.0.0.1:5173/bank-sync"
        }

        url = f"{self.base_url}/v2/consents"
        # Log at DEBUG only — never prints at INFO level or above in production
        logger.debug("Setu POST /v2/consents payload: %s", payload)
        res = self._request_with_retry('POST', url, json=payload)
        data = res.json()

        consent_handle = data.get('id') or data.get('consentId') or data.get('consentHandle')
        redirect_url = data.get('url') or data.get('redirectUrl') or (f"{self.base_url}/consent/{consent_handle}" if consent_handle else None)

        if not consent_handle or not redirect_url:
            raise SetuAPIError(f"Setu consent response missing consent handle or redirect URL: {data}", response_body=data, status_code=res.status_code)

        return {
            'consent_handle': consent_handle,
            'redirect_url': redirect_url,
            'raw_response': data
        }

    def get_consent(self, request_id):
        """
        GET /v2/consents/{request_id} — check consent status.
        """
        url = f"{self.base_url}/v2/consents/{request_id}"
        res = self._request_with_retry('GET', url)
        return res.json()

    def revoke_consent(self, request_id):
        """
        POST /v2/consents/{request_id}/revoke — revoke consent.
        """
        url = f"{self.base_url}/v2/consents/{request_id}/revoke"
        res = self._request_with_retry('POST', url)
        return res.status_code in (200, 204)

    def check_consent_fetch_status(self, consent_id):
        """
        GET /v2/consents/{consent_id}/fetch/status — check if FI data fetch is ready.
        """
        url = f"{self.base_url}/v2/consents/{consent_id}/fetch/status"
        res = self._request_with_retry('GET', url)
        return res.json()

    def trigger_session(self, consent_id, start=None, end=None):
        """
        POST /v2/sessions — Step 1 of FI data fetch.
        """
        url = f"{self.base_url}/v2/sessions"
        payload = {
            "consentId": consent_id,
            "format": "json"
        }

        res = self._request_with_retry('POST', url, json=payload)
        data = res.json()
        session_id = data.get('id') or data.get('sessionId')
        if not session_id:
            raise SetuAPIError(f"Setu session creation response missing session ID: {data}", response_body=data)
        return {'session_id': session_id, 'raw': data}

    def poll_session(self, session_id):
        """
        GET /v2/sessions/{session_id} — Step 2 of FI data fetch.
        """
        url = f"{self.base_url}/v2/sessions/{session_id}"
        res = self._request_with_retry('GET', url)
        return res.json()

    def fetch_financial_data(self, consent_id):
        """
        Orchestrates 2-step FI data fetch.
        """
        sess_res = self.trigger_session(consent_id)
        session_id = sess_res['session_id']
        return self.poll_session(session_id)

    def verify_webhook_signature(self, headers, raw_body):
        """
        Verifies Setu HMAC SHA256 webhook signature header.
        """
        signature = (
            headers.get('x-setu-signature') or
            headers.get('X-Setu-Signature') or
            headers.get('HTTP_X_SETU_SIGNATURE')
        )
        if not signature:
            if os.getenv('SETU_SKIP_WEBHOOK_VERIFY', 'False').lower() in ('true', '1'):
                return True
            return False

        try:
            if isinstance(raw_body, dict):
                raw_body_bytes = json.dumps(raw_body, separators=(',', ':')).encode('utf-8')
            elif isinstance(raw_body, str):
                raw_body_bytes = raw_body.encode('utf-8')
            elif isinstance(raw_body, bytes):
                raw_body_bytes = raw_body
            else:
                raw_body_bytes = b''

            expected_sig = hmac.new(
                self.secret_key.encode('utf-8'),
                raw_body_bytes,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            logger.error(f"Error in verify_webhook_signature: {e}")
            return False
