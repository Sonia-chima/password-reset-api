from rest_framework import serializers


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates the body of a POST /password-reset-request call."""

    email = serializers.EmailField()
