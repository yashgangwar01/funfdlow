from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserProfileSerializer, OnboardingSerializer
from categories.services import AllocationService

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Setup default categories for user
            AllocationService.create_default_categories(user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.monthly_salary = serializer.validated_data['monthly_salary']
            user.salary_credit_day = serializer.validated_data['salary_credit_day']
            user.currency = serializer.validated_data['currency']
            user.onboarding_completed = True
            user.save()

            categories_data = serializer.validated_data.get('categories')
            if categories_data:
                AllocationService.update_user_categories_from_onboarding(user, categories_data)

            # Auto-run initial allocation upon completing onboarding
            AllocationService.run_salary_allocation(user)

            return Response({
                'message': 'Onboarding completed successfully',
                'user': UserProfileSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
