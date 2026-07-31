from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from categories.models import Category
from categories.services import AllocationService
from transactions.models import Transaction, BankTransaction, MerchantCategoryMap
from transactions.services import CategoryMatcherService, IngestionEngine, LearningLoopEngine

User = get_user_model()


class AutoDetectedExpenseTrackingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='matcher_user@fundflow.com',
            password='Password123!',
            monthly_salary=Decimal('60000.00'),
            currency='INR'
        )
        AllocationService.create_default_categories(self.user)
        AllocationService.run_salary_allocation(self.user)

        self.groceries = Category.objects.get(user=self.user, name__icontains='Groceries')
        self.entertainment = Category.objects.get(user=self.user, name__icontains='Entertainment')
        self.savings = Category.objects.get(user=self.user, is_savings_category=True)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_category_matcher_tiers(self):
        # Tier (b): Seeded Global Default Pattern
        MerchantCategoryMap.objects.create(
            user=None,
            merchant_pattern='SWIGGY',
            category=self.groceries,
            source='SYSTEM_DEFAULT'
        )

        cat, conf, tier = CategoryMatcherService.match(self.user, 'POS/SWIGGY/BANER/1234', Decimal('350.00'))
        self.assertEqual(cat, self.groceries)
        self.assertEqual(conf, 0.75)
        self.assertEqual(tier, 'SYSTEM_DEFAULT')

        # Tier (a): User Confirmed Pattern (overrides global)
        MerchantCategoryMap.objects.create(
            user=self.user,
            merchant_pattern='SWIGGY',
            category=self.entertainment,
            source='USER_CONFIRMED'
        )

        cat_a, conf_a, tier_a = CategoryMatcherService.match(self.user, 'POS/SWIGGY/BANER/1234', Decimal('350.00'))
        self.assertEqual(cat_a, self.entertainment)
        self.assertEqual(conf_a, 0.95)
        self.assertEqual(tier_a, 'USER_CONFIRMED')

        # Tier (c): Recurring Amount Heuristic
        Transaction.objects.create(
            user=self.user,
            category=self.savings,
            type='EXPENSE',
            amount=Decimal('780.00'),
            date=timezone.now().date() - timedelta(days=10)
        )

        cat_c, conf_c, tier_c = CategoryMatcherService.match(self.user, 'POS/UNKNOWN_GYM/55', Decimal('780.00'), date=timezone.now().date())
        self.assertEqual(cat_c, self.savings)
        self.assertEqual(conf_c, 0.65)
        self.assertEqual(tier_c, 'RECURRING_HEURISTIC')

        # Tier (d): Unmatched Fallback
        cat_d, conf_d, tier_d = CategoryMatcherService.match(self.user, 'POS/COMPLETELY_RANDOM_VENDOR/99', Decimal('12999.00'))
        self.assertIsNone(cat_d)
        self.assertEqual(conf_d, 0.0)
        self.assertEqual(tier_d, 'NONE')

    def test_ingestion_and_correction_learning_loop_with_backlog_resolution(self):
        # 1. Ingest item 1 with unknown merchant -> should be NEEDS_REVIEW
        bt1 = IngestionEngine.process_bank_transaction(self.user, {
            'bank_transaction_ref': 'REF_UNKNOWN_001',
            'raw_narration': 'POS/THE_BLUE_OAK_CAFE/PUNE/101',
            'amount': Decimal('420.00'),
            'date': timezone.now().date()
        })

        self.assertEqual(bt1.status, 'NEEDS_REVIEW')
        self.assertIsNone(bt1.linked_transaction)

        # 2. Ingest item 2 with SAME unknown merchant -> should also be NEEDS_REVIEW
        bt2 = IngestionEngine.process_bank_transaction(self.user, {
            'bank_transaction_ref': 'REF_UNKNOWN_002',
            'raw_narration': 'POS/THE_BLUE_OAK_CAFE/PUNE/102',
            'amount': Decimal('890.00'),
            'date': timezone.now().date()
        })
        self.assertEqual(bt2.status, 'NEEDS_REVIEW')

        # Initial balance of Entertainment
        initial_ent_balance = self.entertainment.current_balance

        # 3. User corrects bt1 to Entertainment category
        LearningLoopEngine.correct_bank_transaction_category(bt1, self.entertainment, self.user)

        bt1.refresh_from_db()
        self.assertEqual(bt1.status, 'CONFIRMED')
        self.assertEqual(bt1.matched_category, self.entertainment)
        self.assertIsNotNone(bt1.linked_transaction)

        # Verify MerchantCategoryMap was created with USER_CONFIRMED
        m_map = MerchantCategoryMap.objects.get(user=self.user, merchant_pattern='THE_BLUE_OAK_CAFE')
        self.assertEqual(m_map.category, self.entertainment)
        self.assertEqual(m_map.source, 'USER_CONFIRMED')

        # 4. Check that backlog item bt2 was AUTOMATICALLY RESOLVED!
        bt2.refresh_from_db()
        self.assertEqual(bt2.status, 'AUTO_MATCHED')
        self.assertEqual(bt2.matched_category, self.entertainment)
        self.assertIsNotNone(bt2.linked_transaction)

        # Verify Entertainment balance was deducted by both (420 + 890 = 1310)
        self.entertainment.refresh_from_db()
        self.assertEqual(self.entertainment.current_balance, initial_ent_balance - Decimal('1310.00'))

    def test_bank_transaction_api_endpoints(self):
        bt = IngestionEngine.process_bank_transaction(self.user, {
            'bank_transaction_ref': 'REF_API_TEST_01',
            'raw_narration': 'POS/RANDOM_MERCHANT/11',
            'amount': Decimal('150.00'),
            'date': timezone.now().date()
        })

        # List pending transactions
        res = self.client.get('/api/v1/bank-transactions/?status=NEEDS_REVIEW')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        # Confirm endpoint
        res_confirm = self.client.post(f'/api/v1/bank-transactions/{bt.id}/confirm/', {'matched_category': self.groceries.id})
        self.assertEqual(res_confirm.status_code, status.HTTP_200_OK)

        bt.refresh_from_db()
        self.assertEqual(bt.status, 'CONFIRMED')

        # Ignore endpoint test
        bt2 = IngestionEngine.process_bank_transaction(self.user, {
            'bank_transaction_ref': 'REF_API_TEST_02',
            'raw_narration': 'INTERNAL_TRANSFER_ACC_99',
            'amount': Decimal('5000.00'),
            'date': timezone.now().date()
        })

        res_ignore = self.client.post(f'/api/v1/bank-transactions/{bt2.id}/ignore/')
        self.assertEqual(res_ignore.status_code, status.HTTP_200_OK)

        bt2.refresh_from_db()
        self.assertEqual(bt2.status, 'IGNORED')

    def test_manual_transaction_creation_disallowed(self):
        # Direct POST creation of manual expense must be rejected with 405 Method Not Allowed
        res = self.client.post('/api/v1/transactions/', {
            'category': self.groceries.id,
            'amount': 500.00,
            'merchant': 'CASH MANUAL VENDOR',
            'type': 'EXPENSE'
        })
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
