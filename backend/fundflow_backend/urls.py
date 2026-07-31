from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions.views import BankTransactionViewSet, MerchantCategoryMapViewSet

bank_router = DefaultRouter()
bank_router.register(r'', BankTransactionViewSet, basename='bank-transaction')

merchant_router = DefaultRouter()
merchant_router.register(r'', MerchantCategoryMapViewSet, basename='merchant-category-map')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/categories/', include('categories.urls')),
    path('api/v1/bank-transactions/', include(bank_router.urls)),
    path('api/v1/merchant-category-map/', include(merchant_router.urls)),
    path('api/v1/bank-sync/', include('bank_sync.urls')),
    path('api/v1/transactions/', include('transactions.urls')),
    path('api/v1/bills/', include('bills.urls')),
    path('api/v1/goals/', include('goals.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/insights/', include('insights.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]
