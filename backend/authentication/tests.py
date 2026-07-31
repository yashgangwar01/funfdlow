from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from categories.models import Category
from categories.services import AllocationService
from transactions.models import Transaction, OverflowRule, AutoTransferLog
from transactions.services import OverflowEngine

User = get_user_model()


class FundFlowCoreEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@fundflow.com',
            password='TestPassword123!',
            monthly_salary=Decimal('50000.00'),
            currency='INR'
        )
        AllocationService.create_default_categories(self.user)

    def test_salary_allocation(self):
        run = AllocationService.run_salary_allocation(self.user)
        self.assertIsNotNone(run)
        self.assertEqual(run.salary_amount, Decimal('50000.00'))

        savings = Category.objects.get(user=self.user, is_savings_category=True)
        # 20% of 50,000 = 10,000
        self.assertEqual(savings.current_balance, Decimal('10000.00'))

    def test_smart_cover_auto_transfer(self):
        AllocationService.run_salary_allocation(self.user)

        groceries = Category.objects.get(user=self.user, name__icontains='Groceries')
        savings = Category.objects.get(user=self.user, is_savings_category=True)

        # Set up Smart Cover rule: Groceries borrows from Savings when balance < 0
        rule = OverflowRule.objects.create(
            category=groceries,
            source_category=savings,
            trigger_threshold=Decimal('0.00'),
            transfer_type='COVER_DEFICIT',
            priority=1,
            is_active=True
        )

        initial_groceries_balance = groceries.current_balance  # 15% of 50k = 7500
        initial_savings_balance = savings.current_balance      # 20% of 50k = 10000

        # Log an expense that exceeds groceries balance by 2500 (total expense = 10000)
        expense_amount = Decimal('10000.00')
        groceries.current_balance -= expense_amount
        groceries.save()

        # Trigger Smart Cover
        log = OverflowEngine.evaluate_and_trigger_smart_cover(self.user, groceries)

        self.assertIsNotNone(log)
        self.assertEqual(log.amount, Decimal('2500.00'))

        groceries.refresh_from_db()
        savings.refresh_from_db()

        # Groceries balance should now be 0.00 (7500 - 10000 + 2500)
        self.assertEqual(groceries.current_balance, Decimal('0.00'))
        # Savings balance should be 7500.00 (10000 - 2500)
        self.assertEqual(savings.current_balance, Decimal('7500.00'))
