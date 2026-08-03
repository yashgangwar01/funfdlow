import re
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Transaction, OverflowRule, AutoTransferLog, BankTransaction, MerchantCategoryMap
from categories.models import Category
from notifications.models import Notification


GENERIC_TRANSACTION_TOKENS = {
    'POS', 'UPI', 'ACH', 'NEFT', 'IMPS', 'REF', 'BILL', 'ATM', 'CARD',
    'CASH', 'OTHERS', 'FT', 'DEBIT', 'CREDIT', 'DE', 'CR', 'DR', 'GENERIC_BANK_FEED', 'UNKNOWN'
}


class MerchantNormalizer:
    @staticmethod
    def normalize(raw_narration):
        if not raw_narration:
            return "UNKNOWN"

        text = raw_narration.strip()

        # 1. Check known brand keywords first
        text_upper = text.upper()
        keywords = [
            'SWIGGY', 'ZOMATO', 'NETFLIX', 'SPOTIFY', 'UBER', 'OLA', 'RAPIDO',
            'AMAZON', 'FLIPKART', 'WALMART', 'LIC', 'HDFC', 'ICICI', 'EMI', 'STARBUCKS'
        ]
        for kw in keywords:
            if kw in text_upper:
                return kw

        # 2. ReBIT multi-part format (e.g. CARD/DE/723795621359/Purab Dar/WFRO/10843854)
        parts = [p.strip() for p in text.split('/') if p.strip()]

        clean_parts = []
        for part in parts:
            part_upper = part.upper()
            # Skip generic prefix mode/indicator tokens
            if part_upper in GENERIC_TRANSACTION_TOKENS:
                continue
            # Skip pure numeric or long reference IDs (e.g. 723795621359)
            if part.isdigit() or (re.match(r'^[0-9A-Z]{8,}$', part_upper) and any(c.isdigit() for c in part)):
                continue
            clean_parts.append(part)

        if clean_parts:
            candidate = clean_parts[0].upper()
            if candidate not in GENERIC_TRANSACTION_TOKENS:
                return candidate

        return "GENERIC_BANK_FEED"


class CategoryMatcherService:
    @staticmethod
    def match(user, raw_narration, amount, date=None):
        normalized_merchant = MerchantNormalizer.normalize(raw_narration)
        user_categories = Category.objects.filter(user=user)

        # Tier (a): User's own MerchantCategoryMap where source='USER_CONFIRMED'
        user_map = MerchantCategoryMap.objects.filter(
            user=user,
            merchant_pattern=normalized_merchant,
            source='USER_CONFIRMED'
        ).first()
        if user_map and user_map.category in user_categories:
            return user_map.category, 0.95, 'USER_CONFIRMED'

        # Tier (b): Seeded global default map of common merchant patterns
        global_map = MerchantCategoryMap.objects.filter(
            user=None,
            merchant_pattern=normalized_merchant,
            source='SYSTEM_DEFAULT'
        ).first()
        if global_map:
            # Find matching category by name or savings flag
            matching_cat = user_categories.filter(name__icontains=global_map.category.name).first()
            if matching_cat:
                return matching_cat, 0.75, 'SYSTEM_DEFAULT'

        # Heuristic search by keywords against category names
        for cat in user_categories:
            cat_name_upper = cat.name.upper()
            if normalized_merchant in cat_name_upper or any(kw in cat_name_upper for kw in normalized_merchant.split()):
                return cat, 0.75, 'SYSTEM_DEFAULT'

        # Default keyword rules for fallback matching
        default_rules = {
            'SWIGGY': 'Groceries', 'ZOMATO': 'Entertainment', 'NETFLIX': 'Entertainment',
            'SPOTIFY': 'Entertainment', 'UBER': 'Transportation', 'OLA': 'Transportation',
            'RAPIDO': 'Transportation', 'EMI': 'Loans', 'LIC': 'Bills', 'RENT': 'Rent'
        }
        for kw, target_cat_substr in default_rules.items():
            if kw in normalized_merchant:
                found_cat = user_categories.filter(name__icontains=target_cat_substr).first()
                if found_cat:
                    return found_cat, 0.75, 'SYSTEM_DEFAULT'

        # Tier (c): Recurring-amount heuristic (same amount + same category paid in the last 60 days)
        if date:
            start_date = date - timedelta(days=60)
            prev_tx = Transaction.objects.filter(
                user=user,
                type='EXPENSE',
                amount=amount,
                date__gte=start_date
            ).first()
            if prev_tx and prev_tx.category in user_categories:
                return prev_tx.category, 0.65, 'RECURRING_HEURISTIC'

        # Tier (d): No match
        return None, 0.0, 'NONE'


class IngestionEngine:
    @staticmethod
    def process_bank_transaction(user, raw_data):
        """
        Creates a BankTransaction, runs CategoryMatcher, and auto-confirms if confidence >= threshold.
        """
        bank_ref = raw_data.get('bank_transaction_ref')
        raw_narration = raw_data.get('raw_narration', '')
        amount = Decimal(str(raw_data.get('amount', 0.0)))
        tx_date = raw_data.get('date') or timezone.now().date()
        tx_type = raw_data.get('type', 'DEBIT')

        normalized_merchant = MerchantNormalizer.normalize(raw_narration)

        with transaction.atomic():
            # Check de-duplication
            existing_bt = BankTransaction.objects.filter(bank_transaction_ref=bank_ref).first()
            if existing_bt:
                return existing_bt

            matched_cat, confidence, tier = CategoryMatcherService.match(user, raw_narration, amount, tx_date)
            auto_threshold = getattr(settings, 'AUTO_CONFIRM_THRESHOLD', 0.85)

            bt = BankTransaction.objects.create(
                user=user,
                bank_transaction_ref=bank_ref,
                raw_narration=raw_narration,
                normalized_merchant=normalized_merchant,
                amount=amount,
                type=tx_type,
                date=tx_date,
                matched_category=matched_cat,
                confidence_score=confidence,
                status='AUTO_MATCHED' if (matched_cat and confidence >= auto_threshold) else 'NEEDS_REVIEW'
            )

            if matched_cat and confidence >= auto_threshold and tx_type == 'DEBIT':
                # Auto-create Transaction
                tx = Transaction.objects.create(
                    user=user,
                    category=matched_cat,
                    type='EXPENSE',
                    source='AUTO_DETECTED',
                    amount=amount,
                    merchant=normalized_merchant,
                    note=f"Auto-Detected from bank: {raw_narration}",
                    bank_transaction=bt
                )

                # Deduct category balance
                matched_cat.current_balance = Decimal(str(matched_cat.current_balance)) - amount
                matched_cat.save()

                # Link transaction & run Overflow Engine
                bt.linked_transaction = tx
                bt.save()

                OverflowEngine.evaluate_and_trigger_smart_cover(user, matched_cat)

            return bt


class LearningLoopEngine:
    @staticmethod
    def correct_bank_transaction_category(bank_transaction, new_category, user):
        """
        Handles user correction / confirmation of a bank transaction.
        Updates category balance, upserts MerchantCategoryMap, and auto-resolves pending backlog items.
        """
        with transaction.atomic():
            old_tx = bank_transaction.linked_transaction

            # Step (a): Reverse previous category balance if a transaction already exists
            if old_tx:
                old_cat = old_tx.category
                old_cat.current_balance = Decimal(str(old_cat.current_balance)) + Decimal(str(old_tx.amount))
                old_cat.save()
                old_tx.delete()

            # Step (b): Create/update Transaction under new_category
            new_tx = Transaction.objects.create(
                user=user,
                category=new_category,
                type='EXPENSE',
                source='USER_CORRECTED',
                amount=bank_transaction.amount,
                merchant=bank_transaction.normalized_merchant,
                note=f"Bank Transaction: {bank_transaction.raw_narration}",
                bank_transaction=bank_transaction
            )

            new_category.current_balance = Decimal(str(new_category.current_balance)) - Decimal(str(bank_transaction.amount))
            new_category.save()

            OverflowEngine.evaluate_and_trigger_smart_cover(user, new_category)

            # Step (c): Upsert MerchantCategoryMap for (user, normalized_merchant)
            if bank_transaction.normalized_merchant not in GENERIC_TRANSACTION_TOKENS:
                m_map, created = MerchantCategoryMap.objects.get_or_create(
                    user=user,
                    merchant_pattern=bank_transaction.normalized_merchant,
                    defaults={
                        'category': new_category,
                        'source': 'USER_CONFIRMED',
                        'match_count': 1
                    }
                )
                if not created:
                    m_map.category = new_category
                    m_map.source = 'USER_CONFIRMED'
                    m_map.match_count += 1
                    m_map.last_confirmed_at = timezone.now()
                    m_map.save()

            # Step (d): Set status = CONFIRMED
            bank_transaction.matched_category = new_category
            bank_transaction.confidence_score = 0.95
            bank_transaction.status = 'CONFIRMED'
            bank_transaction.linked_transaction = new_tx
            bank_transaction.save()

            # Step (e): Re-run Category Matcher on all pending NEEDS_REVIEW items for this user & merchant
            pending_backlog = BankTransaction.objects.filter(
                user=user,
                normalized_merchant=bank_transaction.normalized_merchant,
                status='NEEDS_REVIEW'
            ).exclude(id=bank_transaction.id)

            for pending in pending_backlog:
                # Since user confirmed pattern now exists at Tier (a), confidence will be 0.95 >= 0.85
                matched_cat, confidence, tier = CategoryMatcherService.match(user, pending.raw_narration, pending.amount, pending.date)
                if matched_cat and confidence >= getattr(settings, 'AUTO_CONFIRM_THRESHOLD', 0.85) and pending.type == 'DEBIT':
                    p_tx = Transaction.objects.create(
                        user=user,
                        category=matched_cat,
                        type='EXPENSE',
                        source='AUTO_DETECTED',
                        amount=pending.amount,
                        merchant=pending.normalized_merchant,
                        note=f"Auto-Resolved from learned rule: {pending.raw_narration}",
                        bank_transaction=pending
                    )
                    matched_cat.current_balance = Decimal(str(matched_cat.current_balance)) - Decimal(str(pending.amount))
                    matched_cat.save()

                    pending.matched_category = matched_cat
                    pending.confidence_score = confidence
                    pending.status = 'AUTO_MATCHED'
                    pending.linked_transaction = p_tx
                    pending.save()

                    OverflowEngine.evaluate_and_trigger_smart_cover(user, matched_cat)

            return bank_transaction


class OverflowEngine:
    @staticmethod
    def evaluate_and_trigger_smart_cover(user, category):
        if category.current_balance >= 0:
            rules = OverflowRule.objects.filter(
                category=category,
                is_active=True,
                trigger_threshold__gt=category.current_balance
            ).order_by('priority')
            if not rules.exists():
                return None
        else:
            rules = OverflowRule.objects.filter(
                category=category,
                is_active=True
            ).order_by('priority')

        if not rules.exists():
            return None

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for rule in rules:
            transfers_count = AutoTransferLog.objects.filter(
                rule=rule,
                created_at__gte=month_start
            ).count()

            if transfers_count >= rule.max_transfers_per_month:
                continue

            source_cat = rule.source_category
            if source_cat.current_balance <= 0:
                Notification.objects.create(
                    user=user,
                    type='AUTO_TRANSFER',
                    title='Smart Cover Safety Cap Triggered',
                    message=f"Category '{category.name}' has a shortfall, but source category '{source_cat.name}' has insufficient balance ({user.currency} {source_cat.current_balance}). Transfer aborted."
                )
                continue

            deficit = abs(category.current_balance) if category.current_balance < 0 else (rule.trigger_threshold - category.current_balance)
            if rule.transfer_type == 'FIXED_AMOUNT' and rule.transfer_amount:
                transfer_amt = min(rule.transfer_amount, source_cat.current_balance)
            else:
                transfer_amt = min(deficit, source_cat.current_balance)

            if transfer_amt <= 0:
                continue

            with transaction.atomic():
                source_cat.current_balance = Decimal(str(source_cat.current_balance)) - transfer_amt
                source_cat.save()

                category.current_balance = Decimal(str(category.current_balance)) + transfer_amt
                category.save()

                log = AutoTransferLog.objects.create(
                    user=user,
                    rule=rule,
                    from_category=source_cat,
                    to_category=category,
                    amount=transfer_amt,
                    reason=f"Smart Cover Auto-Transfer to cover shortfall in {category.name}"
                )

                Transaction.objects.create(
                    user=user,
                    category=source_cat,
                    type='AUTO_TRANSFER',
                    amount=transfer_amt,
                    note=f"Smart Cover Transfer Out to {category.name}",
                    merchant='Smart Cover System'
                )

                Transaction.objects.create(
                    user=user,
                    category=category,
                    type='AUTO_TRANSFER',
                    amount=transfer_amt,
                    note=f"Smart Cover Transfer In from {source_cat.name}",
                    merchant='Smart Cover System'
                )

                Notification.objects.create(
                    user=user,
                    type='AUTO_TRANSFER',
                    title='Smart Cover Auto-Transfer Executed',
                    message=f"Auto-transferred {user.currency} {transfer_amt:.2f} from '{source_cat.name}' to cover '{category.name}'."
                )

                return log

        return None
