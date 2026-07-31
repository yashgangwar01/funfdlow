from rest_framework import serializers
from .models import ConsentRequest


class ConsentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRequest
        fields = (
            'id', 'consent_handle', 'status', 'fi_data_range_start',
            'fi_data_range_end', 'redirect_url', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class InitiateConsentSerializer(serializers.Serializer):
    fi_data_range_start = serializers.DateField(required=False)
    fi_data_range_end = serializers.DateField(required=False)
