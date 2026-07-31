from decimal import Decimal
from django.db import transaction
from .models import Category, AllocationRun


DEFAULT_CATEGORIES = [
    {'name': 'Savings & Emergency Fund', 'allocation_type': 'PERCENTAGE', 'allocation_value': 20.00, 'is_savings_category': True, 'color': '#10b981', 'icon': 'PiggyBank', 'order_index': 0},
    {'name': 'Rent & Housing', 'allocation_type': 'PERCENTAGE', 'allocation_value': 30.00, 'is_savings_category': False, 'color': '#6366f1', 'icon': 'Home', 'order_index': 1},
    {'name': 'Groceries & Household', 'allocation_type': 'PERCENTAGE', 'allocation_value': 15.00, 'is_savings_category': False, 'color': '#3b82f6', 'icon': 'ShoppingCart', 'order_index': 2},
    {'name': 'Bills & Utilities', 'allocation_type': 'PERCENTAGE', 'allocation_value': 10.00, 'is_savings_category': False, 'color': '#f59e0b', 'icon': 'Zap', 'order_index': 3},
    {'name': 'Loans & EMIs', 'allocation_type': 'PERCENTAGE', 'allocation_value': 10.00, 'is_savings_category': False, 'color': '#ef4444', 'icon': 'CreditCard', 'order_index': 4},
    {'name': 'Transportation & Fuel', 'allocation_type': 'PERCENTAGE', 'allocation_value': 5.00, 'is_savings_category': False, 'color': '#8b5cf6', 'icon': 'Car', 'order_index': 5},
    {'name': 'Entertainment & Dining', 'allocation_type': 'PERCENTAGE', 'allocation_value': 5.00, 'is_savings_category': False, 'color': '#ec4899', 'icon': 'Film', 'order_index': 6},
    {'name': 'Investments', 'allocation_type': 'PERCENTAGE', 'allocation_value': 5.00, 'is_savings_category': False, 'color': '#14b8a6', 'icon': 'TrendingUp', 'order_index': 7},
]


class AllocationService:
    @staticmethod
    def create_default_categories(user):
        """Creates the default set of spending categories for a newly registered user."""
        categories = []
        for cat in DEFAULT_CATEGORIES:
            c = Category.objects.create(
                user=user,
                name=cat['name'],
                allocation_type=cat['allocation_type'],
                allocation_value=Decimal(str(cat['allocation_value'])),
                is_savings_category=cat['is_savings_category'],
                color=cat['color'],
                icon=cat['icon'],
                order_index=cat['order_index']
            )
            categories.append(c)
        return categories

    @staticmethod
    def update_user_categories_from_onboarding(user, categories_data):
        """Updates or reconfigures user categories during onboarding wizard."""
        with transaction.atomic():
            # Delete existing non-customized categories if desired or update
            Category.objects.filter(user=user).delete()
            for idx, cat_data in enumerate(categories_data):
                Category.objects.create(
                    user=user,
                    name=cat_data.get('name', f'Category {idx+1}'),
                    allocation_type=cat_data.get('allocation_type', 'PERCENTAGE'),
                    allocation_value=Decimal(str(cat_data.get('allocation_value', 0))),
                    is_savings_category=cat_data.get('is_savings_category', False),
                    color=cat_data.get('color', '#6366f1'),
                    icon=cat_data.get('icon', 'Wallet'),
                    order_index=idx
                )

    @staticmethod
    def run_salary_allocation(user):
        """
        Executes monthly salary distribution into category balances atomically.
        Calculates fixed or percentage amounts per category.
        """
        from transactions.models import Transaction

        salary = Decimal(str(user.monthly_salary))
        if salary <= 0:
            return None

        categories = Category.objects.filter(user=user).select_for_update()
        snapshot_details = []

        with transaction.atomic():
            for category in categories:
                if category.allocation_type == 'PERCENTAGE':
                    allocated_amount = (salary * Decimal(str(category.allocation_value))) / Decimal('100.00')
                else:  # FIXED
                    allocated_amount = Decimal(str(category.allocation_value))

                # Add allocated amount to current category balance
                category.current_balance = Decimal(str(category.current_balance)) + allocated_amount
                category.save()

                # Log ALLOCATION transaction
                Transaction.objects.create(
                    user=user,
                    category=category,
                    type='ALLOCATION',
                    amount=allocated_amount,
                    note=f"Monthly Salary Allocation ({category.allocation_value}{'%' if category.allocation_type == 'PERCENTAGE' else user.currency})",
                    merchant='Salary Credit'
                )

                snapshot_details.append({
                    'category_id': category.id,
                    'category_name': category.name,
                    'allocation_type': category.allocation_type,
                    'allocation_value': str(category.allocation_value),
                    'allocated_amount': str(allocated_amount),
                    'new_balance': str(category.current_balance)
                })

            run = AllocationRun.objects.create(
                user=user,
                salary_amount=salary,
                status='SUCCESS',
                details={'categories': snapshot_details}
            )
            return run
