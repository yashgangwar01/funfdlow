from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet, UpcomingBillsView

router = DefaultRouter()
router.register(r'', BillViewSet, basename='bill')

urlpatterns = [
    path('upcoming/', UpcomingBillsView.as_view(), name='upcoming_bills'),
    path('', include(router.urls)),
]
