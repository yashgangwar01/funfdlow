from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction as db_transaction
from .models import Transaction, OverflowRule, AutoTransferLog, BankTransaction, MerchantCategoryMap
from .serializers import (
    TransactionSerializer, OverflowRuleSerializer, AutoTransferLogSerializer,
    BankTransactionSerializer, MerchantCategoryMapSerializer, IngestBankTransactionsSerializer
)
from .services import OverflowEngine, IngestionEngine, LearningLoopEngine
from categories.models import Category


class BankTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = BankTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = BankTransaction.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        cat_id = request.data.get('matched_category')
        if cat_id:
            try:
                new_cat = Category.objects.get(id=cat_id, user=request.user)
                updated_bt = LearningLoopEngine.correct_bank_transaction_category(instance, new_cat, request.user)
                return Response(BankTransactionSerializer(updated_bt).data)
            except Category.DoesNotExist:
                return Response({'error': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        bt = self.get_object()
        cat_id = request.data.get('matched_category') or (bt.matched_category.id if bt.matched_category else None)
        if not cat_id:
            return Response({'error': 'No category specified for confirmation'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = Category.objects.get(id=cat_id, user=request.user)
            updated_bt = LearningLoopEngine.correct_bank_transaction_category(bt, category, request.user)
            return Response({
                'message': 'Transaction confirmed & merchant pattern learned',
                'bank_transaction': BankTransactionSerializer(updated_bt).data
            })
        except Category.DoesNotExist:
            return Response({'error': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='ignore')
    def ignore(self, request, pk=None):
        bt = self.get_object()
        with db_transaction.atomic():
            if bt.linked_transaction:
                old_tx = bt.linked_transaction
                cat = old_tx.category
                cat.current_balance = Decimal(str(cat.current_balance)) + Decimal(str(old_tx.amount))
                cat.save()
                old_tx.delete()
                bt.linked_transaction = None

            bt.status = 'IGNORED'
            bt.save()

        return Response({'message': 'Bank transaction marked as ignored', 'bank_transaction': BankTransactionSerializer(bt).data})

    @action(detail=False, methods=['post'], url_path='ingest')
    def ingest(self, request):
        serializer = IngestBankTransactionsSerializer(data=request.data)
        if serializer.is_valid():
            tx_data_list = serializer.validated_data['transactions']
            results = []
            for item in tx_data_list:
                bt = IngestionEngine.process_bank_transaction(request.user, item)
                results.append(BankTransactionSerializer(bt).data)
            return Response({'message': f"Ingested {len(results)} bank transactions", 'transactions': results}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MerchantCategoryMapViewSet(viewsets.ModelViewSet):
    serializer_class = MerchantCategoryMapSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MerchantCategoryMap.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, source='USER_CONFIRMED')


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'head', 'options', 'delete']

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        category_id = self.request.query_params.get('category')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset

    def perform_create(self, serializer):
        with db_transaction.atomic():
            tx = serializer.save(user=self.request.user)
            cat = tx.category
            if tx.type == 'EXPENSE':
                cat.current_balance = Decimal(str(cat.current_balance)) - Decimal(str(tx.amount))
                cat.save()
                OverflowEngine.evaluate_and_trigger_smart_cover(self.request.user, cat)
            elif tx.type == 'ALLOCATION' or tx.type == 'ADJUSTMENT':
                cat.current_balance = Decimal(str(cat.current_balance)) + Decimal(str(tx.amount))
                cat.save()

    def perform_destroy(self, instance):
        with db_transaction.atomic():
            cat = instance.category
            if instance.type == 'EXPENSE':
                cat.current_balance = Decimal(str(cat.current_balance)) + Decimal(str(instance.amount))
                cat.save()
            instance.delete()


class OverflowRuleViewSet(viewsets.ModelViewSet):
    serializer_class = OverflowRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OverflowRule.objects.filter(category__user=self.request.user)


class AutoTransferLogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs = AutoTransferLog.objects.filter(user=request.user)
        serializer = AutoTransferLogSerializer(logs, many=True)
        return Response(serializer.data)
