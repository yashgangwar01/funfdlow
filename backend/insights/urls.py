from django.urls import path
from .views import LatestInsightsView, GenerateInsightsView

urlpatterns = [
    path('latest/', LatestInsightsView.as_view(), name='insights_latest'),
    path('generate/', GenerateInsightsView.as_view(), name='insights_generate'),
]
