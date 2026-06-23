import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class PasswordResetToken(models.Model):
    """A single-use, time-limited token for resetting a user's password.

    Tokens expire EXPIRY_MINUTES after creation. A token is only valid while it
    is both unused and unexpired.
    """

    # How long a freshly created token remains valid.
    EXPIRY_MINUTES = 15

    email = models.EmailField(
        help_text="Email address the reset token was issued for.",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Cryptographically secure, URL-safe token string.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(
        default=False,
        help_text="Set once the token has been consumed by a confirm request.",
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PasswordResetToken(email={self.email!r}, used={self.is_used})"

    @staticmethod
    def generate_token():
        """Return a new cryptographically secure, URL-safe token string."""
        return secrets.token_urlsafe(48)

    @property
    def expires_at(self):
        """The moment this token stops being valid."""
        return self.created_at + timedelta(minutes=self.EXPIRY_MINUTES)

    def is_expired(self):
        """True if the 15-minute validity window has passed."""
        return timezone.now() >= self.expires_at

    def is_valid(self):
        """True only while the token is both unused and unexpired."""
        return not self.is_used and not self.is_expired()
