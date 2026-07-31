from rest_framework import serializers
from .models import Category, AllocationRun


class CategorySerializer(serializers.ModelSerializer):
    allocated_monthly_amount = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'allocation_type', 'allocation_value',
            'current_balance', 'is_savings_category', 'color', 'icon',
            'order_index', 'allocated_monthly_amount', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_allocated_monthly_amount(self, obj):
        user_salary = float(obj.user.monthly_salary) if obj.user else 0
        if obj.allocation_type == 'PERCENTAGE':
            return round((user_salary * float(obj.allocation_value)) / 100.0, 2)
        return float(obj.allocation_value)


class AllocationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationRun
        fields = ('id', 'salary_amount', 'run_date', 'status', 'details')


class ReorderCategoriesSerializer(serializers.Serializer):
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
