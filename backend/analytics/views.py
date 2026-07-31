from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .services import AnalyticsService


class SummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        summary = AnalyticsService.get_summary(
            request.user,
            month=int(month) if month else None,
            year=int(year) if year else None
        )
        return Response(summary)


class TrendsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        range_months = request.query_params.get('range', '6m')
        num_months = 6
        if range_months == '3m':
            num_months = 3
        elif range_months == '12m':
            num_months = 12

        trends = AnalyticsService.get_trends(request.user, range_months=num_months)
        return Response(trends)


class CategoryBreakdownView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        breakdown = AnalyticsService.get_category_breakdown(request.user)
        return Response(breakdown)


class ExportCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return AnalyticsService.generate_csv(request.user)
