import json
import logging
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

logger = logging.getLogger(__name__)


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

        # Handle direct FI data payload inline if present
        fi_data = payload.get('financialData') or payload.get('DepositJSON') or payload.get('accounts')

        if consent:
            new_status = payload.get('status') or payload.get('consentStatus')
            if new_status in ('APPROVED', 'ACTIVE', 'CONSENT_APPROVED'):
                consent.status = 'APPROVED'
                consent.save(update_fields=['status', 'updated_at'])
                # Only trigger separate session poll if fi_data was not included in webhook
                if not fi_data:
                    try:
                        process_setu_payload(user_id=consent.user.id, consent_id=consent.id)
                    except Exception as e:
                        logger.warning(f"Setu session fetch from webhook skipped/failed for {consent.consent_handle}: {e}")

            elif new_status in ('REJECTED', 'EXPIRED', 'REVOKED'):
                consent.status = new_status if new_status in ('REJECTED', 'EXPIRED') else 'REJECTED'
                consent.save(update_fields=['status', 'updated_at'])

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
            now = timezone.now().date()
            start = serializer.validated_data.get('fi_data_range_start') or (now - timezone.timedelta(days=90))
            end = serializer.validated_data.get('fi_data_range_end') or now

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


def check_and_update_consent_status(consent):
    """
    Checks Setu API for consent status if PENDING, or triggers data fetch if APPROVED but unsynced.
    """
    if consent.status == 'PENDING':
        logger.info(f"🔍 [AUTO-SYNC POLL] Checking consent status for consent_id={consent.id} (handle={consent.consent_handle}) user={consent.user.email}")
        try:
            client = SetuAAClient()
            setu_data = client.get_consent(consent.consent_handle)
            setu_status = setu_data.get('status') or (setu_data.get('detail') or {}).get('status') or ''
            logger.info(f"📊 [AUTO-SYNC POLL] Setu status for {consent.consent_handle} is '{setu_status}'")

            if setu_status.upper() in ('ACTIVE', 'APPROVED', 'CONSENT_APPROVED'):
                logger.info(f"✨ [AUTO-SYNC POLL] Consent {consent.consent_handle} is APPROVED on Setu! Updating DB status and fetching data...")
                consent.status = 'APPROVED'
                consent.save(update_fields=['status', 'updated_at'])
                try:
                    count = process_setu_payload(user_id=consent.user.id, consent_id=consent.id)
                    logger.info(f"🎉 [AUTO-SYNC POLL] Successfully fetched and ingested {count} BankTransaction records for user {consent.user.email} (consent={consent.consent_handle})")
                except Exception as e:
                    logger.error(f"❌ [AUTO-SYNC POLL] Error during automatic data sync of approved consent {consent.consent_handle}: {e}")
                    consent.last_synced_at = timezone.now()
                    consent.save(update_fields=['last_synced_at', 'updated_at'])
            elif setu_status.upper() in ('REJECTED', 'REVOKED', 'EXPIRED'):
                logger.info(f"🛑 [AUTO-SYNC POLL] Consent {consent.consent_handle} was {setu_status}. Updating DB status...")
                consent.status = 'REJECTED' if setu_status.upper() != 'EXPIRED' else 'EXPIRED'
                consent.save(update_fields=['status', 'updated_at'])
            else:
                logger.info(f"⏳ [AUTO-SYNC POLL] Consent {consent.consent_handle} remains in '{setu_status}' state on Setu. Waiting for user approval on webview...")
        except Exception as e:
            logger.warning(f"⚠️ [AUTO-SYNC POLL] Failed auto-check of Setu consent status for {consent.consent_handle}: {e}")

    elif consent.status == 'APPROVED' and consent.last_synced_at is None:
        logger.info(f"⚡ [AUTO-SYNC POLL] Found APPROVED-but-UNSYNCED consent_id={consent.id} (handle={consent.consent_handle}) for user={consent.user.email}. Triggering automatic fetch pipeline...")
        try:
            count = process_setu_payload(user_id=consent.user.id, consent_id=consent.id)
            logger.info(f"🎉 [AUTO-SYNC POLL] Successfully fetched and ingested {count} BankTransaction records for user {consent.user.email} (consent={consent.consent_handle})")
        except Exception as e:
            logger.error(f"❌ [AUTO-SYNC POLL] Error during automatic sync of unsynced consent {consent.consent_handle}: {e}")
            consent.last_synced_at = timezone.now()
            consent.save(update_fields=['last_synced_at', 'updated_at'])


class ConsentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_consents = ConsentRequest.objects.filter(user=request.user)
        # Check consents that are PENDING or APPROVED-but-UNSYNCED
        from django.db.models import Q
        pending_or_unsynced = user_consents.filter(
            Q(status='PENDING') | Q(status='APPROVED', last_synced_at__isnull=True)
        )
        for consent in pending_or_unsynced:
            check_and_update_consent_status(consent)

        # Re-query updated consents
        consents = ConsentRequest.objects.filter(user=request.user)
        return Response(ConsentRequestSerializer(consents, many=True).data)


class ManualSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.db.models import Q
        user_consents = ConsentRequest.objects.filter(user=request.user)
        for consent in user_consents.filter(Q(status='PENDING') | Q(status='APPROVED', last_synced_at__isnull=True)):
            check_and_update_consent_status(consent)

        active_consent = user_consents.filter(status='APPROVED').first()
        if not active_consent:
            active_consent = user_consents.first()
            if not active_consent:
                return Response({'error': 'No bank consent found. Please link your bank account first.'}, status=status.HTTP_400_BAD_REQUEST)

        count = 0
        try:
            count = process_setu_payload(user_id=request.user.id, consent_id=active_consent.id)
        except Exception as e:
            logger.error(f"Manual sync failed for {active_consent.consent_handle}: {e}")

        return Response({
            'message': f'Bank sync complete. Ingested {count} transactions into your Review Inbox.',
            'consent_handle': active_consent.consent_handle,
            'ingested_count': count
        })
