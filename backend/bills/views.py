from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Bill
from .serializers import BillSerializer
from transactions.models import Transaction
from transactions.services import OverflowEngine


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        bill = self.get_object()
        if bill.is_paid:
            return Response({'message': 'Bill is already marked as paid'}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            bill.is_paid = True
            bill.last_paid_date = timezone.now().date()
            bill.save()

            # Create expense transaction if category is linked
            if bill.category:
                tx = Transaction.objects.create(
                    user=request.user,
                    category=bill.category,
                    type='EXPENSE',
                    amount=bill.amount,
                    note=f"Bill Paid: {bill.name}",
                    merchant=bill.name
                )

                cat = bill.category
                cat.current_balance = Decimal(str(cat.current_balance)) - Decimal(str(bill.amount))
                cat.save()

                # Trigger Smart Cover check if needed
                OverflowEngine.evaluate_and_trigger_smart_cover(request.user, cat)

            return Response({
                'message': f"Bill '{bill.name}' marked as paid",
                'bill': BillSerializer(bill).data
            })


class UpcomingBillsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        upcoming = Bill.objects.filter(
            user=request.user,
            is_paid=False,
            due_date__gte=today
        ).order_by('due_date')[:5]
        return Response(BillSerializer(upcoming, many=True).data)
