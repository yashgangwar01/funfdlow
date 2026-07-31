from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'full_name', 'monthly_salary', 'currency')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            monthly_salary=validated_data.get('monthly_salary', 0.00),
            currency=validated_data.get('currency', 'INR')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'monthly_salary', 'salary_credit_day', 'currency', 'onboarding_completed', 'created_at')
        read_only_fields = ('id', 'email', 'created_at')


class OnboardingSerializer(serializers.Serializer):
    monthly_salary = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    salary_credit_day = serializers.IntegerField(min_value=1, max_value=31)
    currency = serializers.CharField(max_length=10, default='INR')
    categories = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
