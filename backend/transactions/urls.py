from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, OverflowRuleViewSet, AutoTransferLogView, BankTransactionViewSet, MerchantCategoryMapViewSet

router = DefaultRouter()
router.register(r'bank-transactions', BankTransactionViewSet, basename='bank-transaction')
router.register(r'merchant-category-map', MerchantCategoryMapViewSet, basename='merchant-category-map')
router.register(r'overflow-rules', OverflowRuleViewSet, basename='overflow-rule')
router.register(r'', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('auto-transfer-logs/', AutoTransferLogView.as_view(), name='auto_transfer_logs'),
    path('', include(router.urls)),
]
