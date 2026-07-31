import re
from rest_framework import serializers
from .models import ConsentRequest
from .aa_providers import VALID_AA_HANDLES


class ConsentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRequest
        fields = (
            'id', 'consent_handle', 'status', 'fi_data_range_start',
            'fi_data_range_end', 'redirect_url', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class InitiateConsentSerializer(serializers.Serializer):
    # VUA = Virtual User Address, e.g. "9999999999@onemoney"
    vua = serializers.CharField(required=True, max_length=100)
    fi_data_range_start = serializers.DateField(required=False)
    fi_data_range_end = serializers.DateField(required=False)

    def validate_vua(self, value):
        value = value.strip()
        # Must match phone_digits@aa_handle pattern
        match = re.fullmatch(r'(\d{10})@([a-z0-9_-]+)', value)
        if not match:
            raise serializers.ValidationError(
                "VUA must be in the format '10digitphone@aaprovider', e.g. '9999999999@onemoney'"
            )
        aa_handle = match.group(2)
        if aa_handle not in VALID_AA_HANDLES:
            raise serializers.ValidationError(
                f"AA provider '{aa_handle}' is not supported. Valid providers: {sorted(VALID_AA_HANDLES)}"
            )
        return value
