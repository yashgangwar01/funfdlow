import json
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import ConsentRequest
from .serializers import ConsentRequestSerializer, InitiateConsentSerializer
from .setu_client import SetuAAClient
from .tasks import process_setu_payload
from .mappers import parse_setu_fi_data_response
from .aa_providers import AA_PROVIDERS
from transactions.services import IngestionEngine


class WebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client = SetuAAClient()

        raw_body = getattr(getattr(request, '_request', request), 'body', b'')
        if not raw_body and hasattr(request, 'data') and request.data:
            raw_body = request.data

        headers = request.headers
        if hasattr(request, 'META'):
            headers = {**request.headers, **request.META}

        # Step 1: Signature Verification
        if not client.verify_webhook_signature(headers, raw_body):
            return Response({'error': 'Invalid request signature'}, status=status.HTTP_401_UNAUTHORIZED)

        if isinstance(raw_body, dict):
            payload = raw_body
        else:
            try:
                payload = json.loads(raw_body.decode('utf-8') if isinstance(raw_body, bytes) else str(raw_body))
            except Exception:
                payload = request.data if hasattr(request, 'data') else {}

        consent_handle = (
            payload.get('consentHandle') or
            payload.get('consentId') or
            payload.get('id')
        )

        consent = None
        if consent_handle:
            consent = ConsentRequest.objects.filter(consent_handle=consent_handle).first()

        if consent:
            new_status = payload.get('status') or payload.get('consentStatus')
            if new_status in ('APPROVED', 'ACTIVE', 'CONSENT_APPROVED'):
                consent.status = 'APPROVED'
                consent.save()
                try:
                    process_setu_payload.delay(user_id=consent.user.id, consent_id=consent.id)
                except Exception:
                    process_setu_payload(user_id=consent.user.id, consent_id=consent.id)

            elif new_status in ('REJECTED', 'EXPIRED', 'REVOKED'):
                consent.status = new_status if new_status in ('REJECTED', 'EXPIRED') else 'REJECTED'
                consent.save()

        # Handle direct FI data payload inline if present
        fi_data = payload.get('financialData') or payload.get('DepositJSON') or payload.get('accounts')
        if fi_data and consent:
            mapped_txs = parse_setu_fi_data_response({'payload': fi_data}, consent.user, consent)
            for mapped_tx in mapped_txs:
                IngestionEngine.process_bank_transaction(consent.user, mapped_tx)

        return Response({'status': 'SUCCESS'}, status=status.HTTP_200_OK)


class FIPListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        aa_filter = request.query_params.get('aa')
        status_filter = request.query_params.get('status')
        client = SetuAAClient()
        fips_data = client.list_fips(aa=aa_filter, status=status_filter)
        return Response(fips_data)


class AAProvidersView(APIView):
    """Returns the list of supported AA providers for the frontend dropdown."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(AA_PROVIDERS)

class ConsentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiateConsentSerializer(data=request.data)
        if serializer.is_valid():
            vua = serializer.validated_data['vua']
            start = serializer.validated_data.get('fi_data_range_start')
            end = serializer.validated_data.get('fi_data_range_end')

            client = SetuAAClient()
            setu_res = client.create_consent_request(request.user, vua=vua, date_range_start=start, date_range_end=end)

            consent_handle = setu_res['consent_handle']
            redirect_url = setu_res['redirect_url']

            consent = ConsentRequest.objects.create(
                user=request.user,
                consent_handle=consent_handle,
                status='PENDING',
                fi_data_range_start=start,
                fi_data_range_end=end,
                redirect_url=redirect_url
            )

            return Response({
                'message': 'Consent request created (Setu v2)',
                'consent': ConsentRequestSerializer(consent).data,
                'redirect_url': redirect_url
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        consents = ConsentRequest.objects.filter(user=request.user)
        return Response(ConsentRequestSerializer(consents, many=True).data)


class ManualSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        active_consent = ConsentRequest.objects.filter(user=request.user, status='APPROVED').first()
        if not active_consent:
            active_consent = ConsentRequest.objects.filter(user=request.user).first()
            if not active_consent:
                return Response({'error': 'No bank consent found. Please link your bank account first.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process_setu_payload.delay(user_id=request.user.id, consent_id=active_consent.id)
        except Exception:
            process_setu_payload(user_id=request.user.id, consent_id=active_consent.id)

        return Response({
            'message': 'Bank sync session triggered. Transactions will appear in your Review Inbox.',
            'consent_handle': active_consent.consent_handle
        })
