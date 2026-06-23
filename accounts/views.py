from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetToken
from .serializers import PasswordResetRequestSerializer
from .services import send_password_reset_email
from .throttles import PasswordResetRequestThrottle

User = get_user_model()


class PasswordResetRequestView(APIView):
    """POST /password-reset-request

    Accepts an email and, if it belongs to a real account, issues a secure
    reset token and "sends" a reset email. The response is always a generic
    200 regardless of whether the email exists, to avoid leaking which
    addresses are registered (email enumeration).
    """

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]

    # Same message whether or not the account exists (anti-enumeration).
    GENERIC_MESSAGE = (
        "If an account with that email exists, a password reset link has "
        "been sent."
    )

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Only do work when the email maps to a real user, but never reveal
        # the outcome to the caller.
        if User.objects.filter(email__iexact=email).exists():
            reset_token = PasswordResetToken.objects.create(
                email=email,
                token=PasswordResetToken.generate_token(),
            )
            send_password_reset_email(email, reset_token.token)

        return Response(
            {"message": self.GENERIC_MESSAGE},
            status=status.HTTP_200_OK,
        )

    def throttled(self, request, wait):
        """Return a clear 429 message when the rate limit is exceeded."""
        # Build the exception with a dict body (DRF would otherwise try to
        # string-join `wait` text onto it), then attach `wait` separately so
        # the Retry-After header is still sent.
        exc = Throttled(
            detail={
                "message": (
                    "Too many password reset requests. Please wait before "
                    "trying again."
                ),
                "retry_after_seconds": int(wait) if wait else None,
            },
        )
        exc.wait = wait
        raise exc

from .serializers import PasswordResetConfirmSerializer

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        try:
            reset_token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not reset_token.is_valid():
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=reset_token.email)
            user.set_password(new_password)
            user.save()
        except User.DoesNotExist:
            return Response(
                {"detail": "User account not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        reset_token.is_used = True
        reset_token.save()
        return Response(
            {"message": "Password has been successfully reset."},
            status=status.HTTP_200_OK
        )
