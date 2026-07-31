from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from categories.models import Category
from categories.services import AllocationService
from transactions.models import Transaction, OverflowRule, BankTransaction, MerchantCategoryMap
from transactions.services import IngestionEngine
from bills.models import Bill
from goals.models import Goal
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds demo user, categories, transactions, overflow rules, bank transactions, and goals for FundFlow.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding FundFlow demo data...")

        email = "demo@fundflow.com"
        password = "Password123!"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': 'Alex Morgan',
                'monthly_salary': Decimal('75000.00'),
                'salary_credit_day': 1,
                'currency': 'INR',
                'onboarding_completed': True
            }
        )

        if created:
            user.set_password(password)
            user.save()

        if not Category.objects.filter(user=user).exists():
            AllocationService.create_default_categories(user)

        AllocationService.run_salary_allocation(user)

        savings = Category.objects.filter(user=user, is_savings_category=True).first()
        rent = Category.objects.filter(user=user, name__icontains='Rent').first()
        groceries = Category.objects.filter(user=user, name__icontains='Groceries').first()
        bills = Category.objects.filter(user=user, name__icontains='Bills').first()
        dining = Category.objects.filter(user=user, name__icontains='Entertainment').first()

        if groceries and savings:
            OverflowRule.objects.get_or_create(
                category=groceries,
                source_category=savings,
                defaults={'trigger_threshold': Decimal('0.00'), 'transfer_type': 'COVER_DEFICIT', 'priority': 1, 'is_active': True}
            )

        if dining and savings:
            OverflowRule.objects.get_or_create(
                category=dining,
                source_category=savings,
                defaults={'trigger_threshold': Decimal('500.00'), 'transfer_type': 'FIXED_AMOUNT', 'transfer_amount': Decimal('1500.00'), 'priority': 2, 'is_active': True}
            )

        # Seed global default merchant category patterns
        if groceries:
            MerchantCategoryMap.objects.get_or_create(
                user=None, merchant_pattern='SWIGGY',
                defaults={'category': groceries, 'source': 'SYSTEM_DEFAULT', 'match_count': 100}
            )
        if dining:
            MerchantCategoryMap.objects.get_or_create(
                user=None, merchant_pattern='NETFLIX',
                defaults={'category': dining, 'source': 'SYSTEM_DEFAULT', 'match_count': 100}
            )

        # Ingest sample Bank Transactions
        now = timezone.now().date()
        bank_samples = [
            {'bank_transaction_ref': 'TXN_SWIGGY_101', 'raw_narration': 'POS/SWIGGY/BANER/44021', 'amount': Decimal('450.00'), 'date': now - timedelta(days=1)},
            {'bank_transaction_ref': 'TXN_NETFLIX_102', 'raw_narration': 'UPI/NETFLIX/SUBSCRIPTION/88', 'amount': Decimal('649.00'), 'date': now - timedelta(days=2)},
            {'bank_transaction_ref': 'TXN_UNKNOWN_103', 'raw_narration': 'POS/THE_BLUE_OAK_CAFE/99', 'amount': Decimal('1250.00'), 'date': now - timedelta(days=3)},
            {'bank_transaction_ref': 'TXN_UNKNOWN_104', 'raw_narration': 'POS/THE_BLUE_OAK_CAFE/102', 'amount': Decimal('890.00'), 'date': now - timedelta(days=1)},
        ]

        for sample in bank_samples:
            IngestionEngine.process_bank_transaction(user, sample)

        # Seed Bills & Goals
        if bills:
            Bill.objects.get_or_create(
                user=user, name='High-Speed Wi-Fi', amount=Decimal('1299.00'),
                defaults={'category': bills, 'due_date': now + timedelta(days=4), 'reminder_days_before': 3}
            )

        Goal.objects.get_or_create(
            user=user, name='Emergency Fund (6 Months)', target_amount=Decimal('300000.00'),
            defaults={'current_amount': Decimal('120000.00'), 'target_date': now + timedelta(days=365), 'linked_category': savings}
        )

        self.stdout.write(self.style.SUCCESS("FundFlow demo data with Bank Transactions seeded!"))
