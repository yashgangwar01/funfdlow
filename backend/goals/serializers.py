from rest_framework import serializers
from .models import Goal


class GoalSerializer(serializers.ModelSerializer):
    linked_category_name = serializers.CharField(source='linked_category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    projected_completion_date = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = (
            'id', 'name', 'target_amount', 'current_amount', 'target_date',
            'linked_category', 'linked_category_name', 'progress_percentage',
            'projected_completion_date', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_progress_percentage(self, obj):
        if obj.target_amount <= 0:
            return 100.0
        pct = (float(obj.current_amount) / float(obj.target_amount)) * 100.0
        return round(min(pct, 100.0), 1)

    def get_projected_completion_date(self, obj):
        # Calculate based on linked category balance or current savings rate
        if obj.linked_category and obj.linked_category.current_balance > 0:
            current = float(obj.linked_category.current_balance)
        else:
            current = float(obj.current_amount)

        target = float(obj.target_amount)
        if current >= target:
            return "Achieved"

        user = obj.user
        monthly_saving = (float(user.monthly_salary) * 0.20) if user and user.monthly_salary else 500.0
        if monthly_saving <= 0:
            return "Indefinite"

        months_needed = int((target - current) / monthly_saving) + 1
        return f"~{months_needed} months"
