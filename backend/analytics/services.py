import csv
from decimal import Decimal
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from transactions.models import Transaction
from categories.models import Category


class AnalyticsService:
    @staticmethod
    def get_summary(user, month=None, year=None):
        now = timezone.now()
        cur_month = month or now.month
        cur_year = year or now.year

        transactions = Transaction.objects.filter(
            user=user,
            date__year=cur_year,
            date__month=cur_month
        )

        total_spent = transactions.filter(type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_allocated = transactions.filter(type='ALLOCATION').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if total_allocated == 0:
            total_allocated = Decimal(str(user.monthly_salary))

        savings_category = Category.objects.filter(user=user, is_savings_category=True).first()
        savings_balance = savings_category.current_balance if savings_category else Decimal('0.00')

        total_income = Decimal(str(user.monthly_salary))
        net_savings_rate = round(float((savings_balance / total_income) * 100), 1) if total_income > 0 else 0.0

        return {
            'monthly_salary': float(user.monthly_salary),
            'total_allocated': float(total_allocated),
            'total_spent': float(total_spent),
            'remaining_budget': float(total_allocated - total_spent),
            'savings_balance': float(savings_balance),
            'savings_rate_percentage': net_savings_rate,
            'currency': user.currency,
            'month': cur_month,
            'year': cur_year
        }

    @staticmethod
    def get_trends(user, range_months=6):
        now = timezone.now()
        trends = []

        for i in range(range_months - 1, -1, -1):
            # Calculate month and year
            target_date = now - timedelta(days=i * 30)
            m = target_date.month
            y = target_date.year
            month_label = target_date.strftime('%b %Y')

            txs = Transaction.objects.filter(user=user, date__year=y, date__month=m)
            expenses = txs.filter(type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            allocations = txs.filter(type='ALLOCATION').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            income = float(user.monthly_salary)
            spent = float(expenses)
            saved = max(0.0, income - spent)

            trends.append({
                'month': month_label,
                'income': income,
                'expenses': spent,
                'savings': saved,
                'allocation': float(allocations) if allocations else income
            })

        return trends

    @staticmethod
    def get_category_breakdown(user):
        categories = Category.objects.filter(user=user)
        breakdown = []
        now = timezone.now()

        total_all_spent = Transaction.objects.filter(
            user=user,
            type='EXPENSE',
            date__year=now.year,
            date__month=now.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_all_spent_float = float(total_all_spent)

        for cat in categories:
            spent = Transaction.objects.filter(
                user=user,
                category=cat,
                type='EXPENSE',
                date__year=now.year,
                date__month=now.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            spent_float = float(spent)
            pct = round((spent_float / total_all_spent_float * 100), 1) if total_all_spent_float > 0 else 0.0

            breakdown.append({
                'category_id': cat.id,
                'name': cat.name,
                'color': cat.color,
                'icon': cat.icon,
                'current_balance': float(cat.current_balance),
                'allocated_value': float(cat.allocation_value),
                'allocation_type': cat.allocation_type,
                'total_spent': spent_float,
                'percentage_of_spending': pct
            })

        return breakdown

    @staticmethod
    def generate_csv(user):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="fundflow_transactions_{user.id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Date', 'Type', 'Category', 'Merchant', 'Note', 'Amount', 'Currency'])

        txs = Transaction.objects.filter(user=user).select_related('category').order_by('-date')
        for tx in txs:
            writer.writerow([
                tx.id,
                tx.date.strftime('%Y-%m-%d'),
                tx.type,
                tx.category.name if tx.category else 'N/A',
                tx.merchant,
                tx.note,
                float(tx.amount),
                user.currency
            ])

        return response
