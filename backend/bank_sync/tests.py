import json
import hmac
import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from bank_sync.models import ConsentRequest
from bank_sync.setu_client import SetuAAClient
from bank_sync.mappers import map_setu_transaction_to_bank_transaction, parse_setu_fi_data_response
from categories.models import Category
from categories.services import AllocationService
from transactions.models import BankTransaction

User = get_user_model()


class SetuAAGatewayV2IntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='setu_v2_user@fundflow.com',
            password='Password123!',
            monthly_salary=Decimal('80000.00'),
            currency='INR'
        )
        AllocationService.create_default_categories(self.user)
        AllocationService.run_salary_allocation(self.user)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('bank_sync.setu_client.requests.post')
    def test_access_token_caching_and_refresh(self, mock_auth_post):
        mock_auth_res = MagicMock()
        mock_auth_res.status_code = 200
        mock_auth_res.json.return_value = {'access_token': 'mock_bearer_jwt_token_123'}
        mock_auth_post.return_value = mock_auth_res

        client = SetuAAClient()
        # First call fetches token from orgservice-prod.setu.co
        token1 = client._get_access_token()
        self.assertEqual(token1, 'mock_bearer_jwt_token_123')
        self.assertEqual(mock_auth_post.call_count, 1)

        # Second call reuses cached token without hitting network
        token2 = client._get_access_token()
        self.assertEqual(token2, 'mock_bearer_jwt_token_123')
        self.assertEqual(mock_auth_post.call_count, 1)

        # Force refresh triggers new auth call
        mock_auth_res.json.return_value = {'access_token': 'mock_bearer_jwt_token_456'}
        token3 = client._get_access_token(force_refresh=True)
        self.assertEqual(token3, 'mock_bearer_jwt_token_456')
        self.assertEqual(mock_auth_post.call_count, 2)

    @patch('bank_sync.setu_client.SetuAAClient._request_with_retry')
    def test_create_consent_request_v2_stores_db_row(self, mock_req):
        mock_res = MagicMock()
        mock_res.status_code = 201
        mock_res.json.return_value = {
            'id': 'SETU_V2_HANDLE_9999',
            'url': 'https://fiu-sandbox.setu.co/consent/SETU_V2_HANDLE_9999'
        }
        mock_req.return_value = mock_res

        res = self.client.post('/api/v1/bank-sync/consent/', {})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('redirect_url', res.data)

        consent = ConsentRequest.objects.get(consent_handle='SETU_V2_HANDLE_9999')
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.status, 'PENDING')

    @patch('bank_sync.setu_client.SetuAAClient._request_with_retry')
    def test_two_step_data_session(self, mock_req):
        client = SetuAAClient()

        # Step 1: trigger_session
        res_trigger = MagicMock()
        res_trigger.status_code = 201
        res_trigger.json.return_value = {'id': 'SESS_12345'}

        # Step 2: poll_session
        res_poll = MagicMock()
        res_poll.status_code = 200
        res_poll.json.return_value = {
            'payload': [
                {
                    'account': 'ACC_999',
                    'transactions': [
                        {
                            'transactionId': 'TXN_V2_001',
                            'narration': 'SWIGGY FOOD ORDER',
                            'amount': '350.00',
                            'type': 'DEBIT',
                            'transactionTimestamp': '2026-07-31T10:00:00Z'
                        }
                    ]
                }
            ]
        }
        mock_req.side_effect = [res_trigger, res_poll]

        data = client.fetch_financial_data('CONSENT_777')
        self.assertIn('payload', data)
        self.assertEqual(mock_req.call_count, 2)

    def test_webhook_signature_verification_rejection(self):
        res = self.client.post(
            '/api/v1/bank-sync/webhook/',
            data={'event': 'CONSENT_APPROVED', 'consentHandle': 'SETU_HANDLE_9999'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch.object(SetuAAClient, 'verify_webhook_signature', return_value=True)
    def test_webhook_v2_ingestion(self, mock_verify):
        consent = ConsentRequest.objects.create(
            user=self.user,
            consent_handle='SETU_V2_HANDLE_8888',
            status='PENDING'
        )

        payload = {
            'type': 'CONSENT_APPROVED',
            'consentHandle': 'SETU_V2_HANDLE_8888',
            'status': 'APPROVED',
            'financialData': [
                {
                    'accountNumber': 'ACC_12345',
                    'transactions': [
                        {
                            'txnId': 'SETU_V2_TXN_001',
                            'narration': 'POS/SWIGGY/BANER/44021',
                            'amount': 450.00,
                            'type': 'DEBIT',
                            'valueDate': '2026-07-31'
                        }
                    ]
                }
            ]
        }

        res = self.client.post(
            '/api/v1/bank-sync/webhook/',
            data=payload,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        bt_count = BankTransaction.objects.filter(bank_transaction_ref='SETU_V2_TXN_001').count()
        self.assertEqual(bt_count, 1)

    def test_defensive_mapper_candidates(self):
        # Candidate 1: Standard ReBIT
        sample1 = {
            'txnId': 'REF_1',
            'narration': 'STARBUCKS COFFEE',
            'amount': 380.0,
            'type': 'DEBIT',
            'valueDate': '2026-07-30'
        }
        m1 = map_setu_transaction_to_bank_transaction(sample1, self.user)
        self.assertEqual(m1['bank_transaction_ref'], 'REF_1')
        self.assertEqual(m1['raw_narration'], 'STARBUCKS COFFEE')
        self.assertEqual(m1['amount'], Decimal('380.0'))

        # Candidate 2: Alternate Setu DepositJSON fields
        sample2 = {
            'transactionId': 'REF_2',
            'description': 'SALARY CREDIT',
            'transactionAmount': '75000.00',
            'creditDebitIndicator': 'CREDIT',
            'transactionTimestamp': '2026-07-01T09:00:00Z'
        }
        m2 = map_setu_transaction_to_bank_transaction(sample2, self.user)
        self.assertEqual(m2['bank_transaction_ref'], 'REF_2')
        self.assertEqual(m2['raw_narration'], 'SALARY CREDIT')
        self.assertEqual(m2['amount'], Decimal('75000.00'))
        self.assertEqual(m2['type'], 'CREDIT')
