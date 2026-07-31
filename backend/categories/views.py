from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Category, AllocationRun
from .serializers import CategorySerializer, AllocationRunSerializer, ReorderCategoriesSerializer
from .services import AllocationService


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        serializer = ReorderCategoriesSerializer(data=request.data)
        if serializer.is_valid():
            order_ids = serializer.validated_data['order_ids']
            categories = {c.id: c for c in Category.objects.filter(user=request.user, id__in=order_ids)}
            for index, cat_id in enumerate(order_ids):
                if cat_id in categories:
                    categories[cat_id].order_index = index
                    categories[cat_id].save()
            return Response({'status': 'reordered'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RunAllocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        run = AllocationService.run_salary_allocation(request.user)
        if run:
            return Response({
                'message': 'Salary allocation executed successfully',
                'run': AllocationRunSerializer(run).data
            })
        return Response({'error': 'Monthly salary must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)


class AllocationHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        runs = AllocationRun.objects.filter(user=request.user)
        serializer = AllocationRunSerializer(runs, many=True)
        return Response(serializer.data)
