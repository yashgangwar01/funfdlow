from django.urls import path
from .views import WebhookView, ConsentView, ConsentListView, ManualSyncView, FIPListView, AAProvidersView

urlpatterns = [
    path('webhook/', WebhookView.as_view(), name='bank_sync_webhook'),
    path('consent/', ConsentView.as_view(), name='bank_sync_consent'),
    path('consents/', ConsentListView.as_view(), name='bank_sync_consents_list'),
    path('sync/', ManualSyncView.as_view(), name='bank_sync_manual_sync'),
    path('fips/', FIPListView.as_view(), name='bank_sync_fips_list'),
    path('aa-providers/', AAProvidersView.as_view(), name='bank_sync_aa_providers'),
]
