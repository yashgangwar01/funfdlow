from django.urls import path
from .views import SummaryView, TrendsView, CategoryBreakdownView, ExportCSVView

urlpatterns = [
    path('summary/', SummaryView.as_view(), name='analytics_summary'),
    path('trends/', TrendsView.as_view(), name='analytics_trends'),
    path('category-breakdown/', CategoryBreakdownView.as_view(), name='analytics_category_breakdown'),
    path('export-csv/', ExportCSVView.as_view(), name='analytics_export_csv'),
]
