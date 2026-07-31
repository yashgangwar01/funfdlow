import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from .models import ConsentRequest
from .setu_client import SetuAAClient
from .mappers import parse_setu_fi_data_response
from transactions.services import IngestionEngine

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def process_setu_payload(user_id, consent_id=None, session_id=None):
    """
    Background worker task for Setu v2 2-step FI data session workflow:
    1. trigger_session(consent_handle) -> session_id (if not provided)
    2. poll_session(session_id) -> FIDataFetchResponseV2 payload
    3. parse_setu_fi_data_response -> IngestionEngine.process_bank_transaction
    """
    try:
        user = User.objects.get(id=user_id)
        consent = ConsentRequest.objects.filter(id=consent_id).first() if consent_id else None

        client = SetuAAClient()
        consent_handle = consent.consent_handle if consent else None

        if not session_id and consent_handle:
            sess_res = client.trigger_session(consent_handle)
            session_id = sess_res.get('session_id')

        if not session_id:
            logger.error(f"No session_id or consent_handle available to process Setu payload for user {user.email}")
            return 0

        fi_response = client.poll_session(session_id)
        mapped_transactions = parse_setu_fi_data_response(fi_response, user, consent)

        ingested_count = 0
        for mapped_tx in mapped_transactions:
            IngestionEngine.process_bank_transaction(user, mapped_tx)
            ingested_count += 1

        logger.info(f"Ingested {ingested_count} Setu v2 transactions for user {user.email}")
        return ingested_count
    except Exception as e:
        logger.error(f"Error in process_setu_payload task: {e}")
        raise
