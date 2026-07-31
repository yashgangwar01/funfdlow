from rest_framework import serializers
from .models import Bill


class BillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Bill
        fields = (
            'id', 'category', 'category_name', 'category_color', 'name',
            'amount', 'due_date', 'recurrence', 'reminder_days_before',
            'is_paid', 'last_paid_date', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
