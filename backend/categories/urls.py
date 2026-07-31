from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, RunAllocationView, AllocationHistoryView

router = DefaultRouter()
router.register(r'', CategoryViewSet, basename='category')

urlpatterns = [
    path('run-allocation/', RunAllocationView.as_view(), name='run_allocation'),
    path('allocation-history/', AllocationHistoryView.as_view(), name='allocation_history'),
    path('', include(router.urls)),
]
