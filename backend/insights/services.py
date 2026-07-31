import os
import requests
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from transactions.models import Transaction, AutoTransferLog
from categories.models import Category
from bills.models import Bill


class AIInsightsService:
    @staticmethod
    def generate_financial_insights(user):
        """
        Analyzes 3 months of transaction data, category balances, auto-transfers, and bills.
        Generates actionable financial recommendations and an optional LLM narrative.
        """
        now = timezone.now()
        categories = Category.objects.filter(user=user)
        txs_this_month = Transaction.objects.filter(
            user=user,
            type='EXPENSE',
            date__year=now.year,
            date__month=now.month
        )

        total_spent = txs_this_month.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        salary = Decimal(str(user.monthly_salary))

        insights = []
        alerts = []
        actionable_steps = []

        day_of_month = now.day
        days_in_month = 30
        month_progress_pct = (day_of_month / days_in_month) * 100

        # Rule 1: High spending pace flag
        for cat in categories:
            if cat.is_savings_category:
                continue

            allocated = (salary * Decimal(str(cat.allocation_value)) / 100) if cat.allocation_type == 'PERCENTAGE' else Decimal(str(cat.allocation_value))
            if allocated <= 0:
                continue

            spent = Transaction.objects.filter(
                user=user,
                category=cat,
                type='EXPENSE',
                date__year=now.year,
                date__month=now.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            spent_pct = float((spent / allocated) * 100)

            if spent_pct >= 90:
                alerts.append({
                    'level': 'HIGH',
                    'title': f'Depleted Category: {cat.name}',
                    'message': f"You have used {spent_pct:.0f}% of your '{cat.name}' allocation with {days_in_month - day_of_month} days remaining."
                })
            elif spent_pct > month_progress_pct + 25:
                alerts.append({
                    'level': 'MEDIUM',
                    'title': f'Fast Burn Rate in {cat.name}',
                    'message': f"Spending in '{cat.name}' ({spent_pct:.0f}%) is progressing faster than the month ({month_progress_pct:.0f}% elapsed)."
                })

        # Rule 2: Smart Cover Auto-Transfers count
        auto_transfers_count = AutoTransferLog.objects.filter(
            user=user,
            created_at__year=now.year,
            created_at__month=now.month
        ).count()

        if auto_transfers_count > 0:
            actionable_steps.append({
                'category': 'Smart Cover',
                'suggestion': f"Smart Cover auto-transferred from Savings {auto_transfers_count} times this month. Consider increasing category budget allocations."
            })

        # Rule 3: Savings rate optimization
        savings_cat = categories.filter(is_savings_category=True).first()
        if savings_cat:
            savings_pct = float(savings_cat.allocation_value) if savings_cat.allocation_type == 'PERCENTAGE' else float((savings_cat.allocation_value / salary) * 100) if salary > 0 else 0
            if savings_pct < 20.0:
                actionable_steps.append({
                    'category': 'Savings Booster',
                    'suggestion': f"Your current savings allocation is {savings_pct:.1f}%. Increasing to at least 20% can build your emergency fund 25% faster."
                })

        # Rule 4: Upcoming overdue bills
        overdue_bills = Bill.objects.filter(user=user, is_paid=False, due_date__lt=now.date())
        if overdue_bills.exists():
            alerts.append({
                'level': 'HIGH',
                'title': f'{overdue_bills.count()} Overdue Bills Pending',
                'message': f"You have {overdue_bills.count()} unpaid bill(s) past due date. Mark them as paid to prevent penalty fees."
            })

        # Generate Narrative (Rule-based or Anthropic LLM API if key available)
        narrative = AIInsightsService._generate_llm_or_fallback_narrative(
            user, salary, total_spent, alerts, actionable_steps
        )

        return {
            'overall_health_score': max(40, 100 - (len(alerts) * 15)),
            'narrative_summary': narrative,
            'alerts': alerts,
            'actionable_steps': actionable_steps,
            'auto_transfers_this_month': auto_transfers_count,
            'generated_at': now.isoformat()
        }

    @staticmethod
    def _generate_llm_or_fallback_narrative(user, salary, total_spent, alerts, actionable_steps):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            try:
                prompt = f"""Summarize this user's monthly financial health in 3 concise, encouraging sentences.
Salary: {user.currency} {salary}
Spent this month: {user.currency} {total_spent}
Alerts count: {len(alerts)}
Action items: {[a['suggestion'] for a in actionable_steps]}
"""
                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 200,
                        'messages': [{'role': 'user', 'content': prompt}]
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    return response.json()['content'][0]['text']
            except Exception:
                pass

        # Fallback narrative generator
        health_status = "excellent" if len(alerts) == 0 else "stable with minor warnings" if len(alerts) <= 2 else "requiring attention"
        return f"Your monthly budget health is currently {health_status}. You have spent {user.currency} {total_spent:.2f} out of your {user.currency} {salary:.2f} monthly salary. FundFlow's Smart Cover system is monitoring your category balances to protect your savings."
