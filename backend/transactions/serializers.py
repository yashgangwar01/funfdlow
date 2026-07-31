from rest_framework import serializers
from .models import Transaction, OverflowRule, AutoTransferLog, BankTransaction, MerchantCategoryMap
from categories.models import Category


class BankTransactionSerializer(serializers.ModelSerializer):
    matched_category_name = serializers.CharField(source='matched_category.name', read_only=True)

    class Meta:
        model = BankTransaction
        fields = (
            'id', 'bank_transaction_ref', 'raw_narration', 'normalized_merchant',
            'amount', 'type', 'date', 'matched_category', 'matched_category_name',
            'confidence_score', 'status', 'linked_transaction', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'confidence_score')


class MerchantCategoryMapSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MerchantCategoryMap
        fields = (
            'id', 'merchant_pattern', 'category', 'category_name',
            'match_count', 'last_confirmed_at', 'source'
        )
        read_only_fields = ('id', 'last_confirmed_at')


class IngestBankTransactionsSerializer(serializers.Serializer):
    transactions = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'category', 'category_name', 'category_color', 'category_icon',
            'type', 'source', 'amount', 'note', 'merchant', 'date', 'receipt_tag',
            'is_recurring', 'bank_transaction', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class OverflowRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    source_category_name = serializers.CharField(source='source_category.name', read_only=True)

    class Meta:
        model = OverflowRule
        fields = (
            'id', 'category', 'category_name', 'source_category', 'source_category_name',
            'trigger_threshold', 'transfer_type', 'transfer_amount',
            'max_transfers_per_month', 'priority', 'is_active'
        )


class AutoTransferLogSerializer(serializers.ModelSerializer):
    from_category_name = serializers.CharField(source='from_category.name', read_only=True)
    to_category_name = serializers.CharField(source='to_category.name', read_only=True)

    class Meta:
        model = AutoTransferLog
        fields = (
            'id', 'rule', 'from_category', 'from_category_name',
            'to_category', 'to_category_name', 'amount', 'reason', 'created_at'
        )
