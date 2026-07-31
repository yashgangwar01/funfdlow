from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .services import AIInsightsService


class LatestInsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        insights = AIInsightsService.generate_financial_insights(request.user)
        return Response(insights)


class GenerateInsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        insights = AIInsightsService.generate_financial_insights(request.user)
        return Response(insights)
