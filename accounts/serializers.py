from rest_framework import serializers


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates the body of a POST /password-reset-request call."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates the body of a POST /password-reset-confirm call."""

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data
