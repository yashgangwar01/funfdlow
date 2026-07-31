"""
Setu Account Aggregator FI Data Schema Mapper (v2 API).
Ref: Setu AA OpenAPI Spec — DepositJSON -> DepositJSONAccount -> DepositJSONAccountTransactions -> DepositJSONAccountTransactionsTransaction
"""
import logging
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)


def map_setu_transaction_to_bank_transaction(raw_txn, user, consent_request=None):
    """
    Translates Setu FI DepositJSONAccountTransactionsTransaction into FundFlow's BankTransaction dictionary.

    Defensive Field Candidates:
    - Reference: ['txnId', 'transactionId', 'reference', 'id', 'transactionRefNumber', 'txId']
    - Narration: ['narration', 'description', 'remark', 'narrationText', 'summary', 'memo']
    - Amount: ['amount', 'transactionAmount', 'val', 'amt', 'value']
    - Type: ['type', 'transactionType', 'txnType', 'creditDebitIndicator']
    - Date: ['valueDate', 'transactionTimestamp', 'date', 'txnDate', 'bookingDate']
    """
    if not isinstance(raw_txn, dict):
        logger.warning(f"Raw transaction payload is not a dictionary: {raw_txn}")
        raw_txn = {}

    # Candidate lookups for transaction reference ID
    ref_candidates = ['txnId', 'transactionId', 'reference', 'id', 'transactionRefNumber', 'txId']
    bank_ref = None
    for candidate in ref_candidates:
        if raw_txn.get(candidate):
            bank_ref = str(raw_txn.get(candidate)).strip()
            break

    if not bank_ref:
        logger.warning(f"Setu transaction missing reference ID in candidates {ref_candidates}. Generating fallback ref.")
        bank_ref = f"SETU_TXN_{user.id}_{int(timezone.now().timestamp())}"

    # Candidate lookups for narration
    narration_candidates = ['narration', 'description', 'remark', 'narrationText', 'summary', 'memo']
    narration = None
    for candidate in narration_candidates:
        if raw_txn.get(candidate):
            narration = str(raw_txn.get(candidate)).strip()
            break

    if not narration:
        logger.warning(f"Setu transaction missing raw narration in candidates {narration_candidates}. Using default.")
        narration = "Bank Transaction"

    # Candidate lookups for amount
    amount_candidates = ['amount', 'transactionAmount', 'val', 'amt', 'value']
    raw_amount = None
    for candidate in amount_candidates:
        if raw_txn.get(candidate) is not None:
            raw_amount = raw_txn.get(candidate)
            break

    try:
        amount = Decimal(str(raw_amount)) if raw_amount is not None else Decimal('0.00')
    except (InvalidOperation, TypeError, ValueError):
        logger.warning(f"Setu transaction invalid amount '{raw_amount}'. Defaulting to 0.00.")
        amount = Decimal('0.00')

    # Candidate lookups for type (DEBIT / CREDIT)
    type_candidates = ['type', 'transactionType', 'txnType', 'creditDebitIndicator']
    raw_type = None
    for candidate in type_candidates:
        if raw_txn.get(candidate):
            raw_type = str(raw_txn.get(candidate)).upper().strip()
            break

    tx_type = 'DEBIT'
    if raw_type in ('CREDIT', 'CR'):
        tx_type = 'CREDIT'

    # Candidate lookups for transaction value date
    date_candidates = ['valueDate', 'transactionTimestamp', 'date', 'txnDate', 'bookingDate']
    raw_date = None
    for candidate in date_candidates:
        if raw_txn.get(candidate):
            raw_date = str(raw_txn.get(candidate))
            break

    parsed_date = timezone.now().date()
    if raw_date:
        try:
            if 'T' in raw_date:
                parsed_date = datetime.fromisoformat(raw_date.replace('Z', '+00:00')).date()
            else:
                parsed_date = datetime.strptime(raw_date[:10], '%Y-%m-%d').date()
        except Exception as e:
            logger.warning(f"Failed to parse Setu date '{raw_date}': {e}. Using current date.")

    return {
        'bank_transaction_ref': bank_ref,
        'raw_narration': narration,
        'amount': amount,
        'type': tx_type,
        'date': parsed_date,
        'consent_request': consent_request
    }


def parse_setu_fi_data_response(fi_payload, user, consent_request=None):
    """
    Parses FIDataFetchResponseV2 JSON structure (DepositJSON -> accounts[] -> transactions[]).
    Returns list of mapped BankTransaction dicts ready for IngestionEngine.
    """
    if not fi_payload or not isinstance(fi_payload, dict):
        logger.warning(f"Received empty or non-dict FI payload: {type(fi_payload)}")
        return []

    # Log payload shape for dev diagnostics (JSON vs XML/ETFJSON)
    payload_keys = list(fi_payload.keys())
    logger.info(f"Setu FI response root keys: {payload_keys}")

    accounts = (
        fi_payload.get('payload', []) or
        fi_payload.get('accounts', []) or
        fi_payload.get('DepositJSON', {}).get('account', []) or
        []
    )
    if isinstance(accounts, dict):
        accounts = [accounts]

    mapped_transactions = []
    for acc in accounts:
        txns = (
            acc.get('transactions', []) or
            acc.get('Transactions', {}).get('Transaction', []) or
            []
        )
        if isinstance(txns, dict):
            txns = [txns]

        for raw_tx in txns:
            mapped_tx = map_setu_transaction_to_bank_transaction(raw_tx, user, consent_request)
            mapped_transactions.append(mapped_tx)

    return mapped_transactions
