"""Side-effecting helpers for the accounts app.

For this assignment, "sending" an email is simulated by printing the reset
details to the console instead of using a real mail backend.
"""

from .models import PasswordResetToken


def send_password_reset_email(email, token):
    """Simulate sending a password-reset email by printing to the console."""
    reset_link = f"https://example.com/password-reset-confirm?token={token}"

    print("=" * 70)
    print("[SIMULATED EMAIL] Password reset requested")
    print(f"  To:      {email}")
    print(f"  Link:    {reset_link}")
    print(f"  Expires: in {PasswordResetToken.EXPIRY_MINUTES} minutes")
    print("=" * 70)
