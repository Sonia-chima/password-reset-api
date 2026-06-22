from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PasswordResetToken

User = get_user_model()


class PasswordResetRequestEndpointTests(APITestCase):
    """Tests for POST /password-reset-request."""

    def setUp(self):
        # Throttling state lives in the cache; clear it so each test starts
        # with a fresh rate-limit budget.
        cache.clear()
        self.url = reverse('password-reset-request')
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='super-secret-pw',
        )

    def test_valid_email_returns_200_and_creates_token(self):
        response = self.client.post(
            self.url, {'email': 'alice@example.com'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        # Exactly one token should have been issued for this email.
        tokens = PasswordResetToken.objects.filter(email='alice@example.com')
        self.assertEqual(tokens.count(), 1)
        self.assertTrue(tokens.first().token)

    def test_email_match_is_case_insensitive(self):
        response = self.client.post(
            self.url, {'email': 'ALICE@example.com'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordResetToken.objects.count(), 1)

    def test_nonexistent_email_still_returns_200_without_token(self):
        response = self.client.post(
            self.url, {'email': 'nobody@example.com'}, format='json'
        )

        # Generic success response (anti-enumeration), but no token created.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(PasswordResetToken.objects.count(), 0)

    def test_response_message_is_identical_for_known_and_unknown_email(self):
        known = self.client.post(
            self.url, {'email': 'alice@example.com'}, format='json'
        )
        cache.clear()  # avoid throttling interfering with the second call
        unknown = self.client.post(
            self.url, {'email': 'nobody@example.com'}, format='json'
        )

        self.assertEqual(known.data['message'], unknown.data['message'])

    def test_invalid_email_returns_400(self):
        response = self.client.post(
            self.url, {'email': 'not-an-email'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limit_returns_429_after_five_requests(self):
        payload = {'email': 'nobody@example.com'}

        # First 5 requests are within the per-hour budget.
        for i in range(5):
            response = self.client.post(self.url, payload, format='json')
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f'request #{i + 1} should be allowed',
            )

        # The 6th request exceeds 5/hour and must be throttled.
        throttled = self.client.post(self.url, payload, format='json')
        self.assertEqual(
            throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )
        self.assertIn('message', throttled.data)


class PasswordResetTokenModelTests(APITestCase):
    """Tests for the token model's expiry / validity logic."""

    def test_fresh_token_is_valid_and_not_expired(self):
        token = PasswordResetToken.objects.create(
            email='alice@example.com',
            token=PasswordResetToken.generate_token(),
        )

        self.assertFalse(token.is_expired())
        self.assertTrue(token.is_valid())

    def test_token_older_than_15_minutes_is_expired(self):
        token = PasswordResetToken.objects.create(
            email='alice@example.com',
            token=PasswordResetToken.generate_token(),
        )
        # created_at uses auto_now_add, so push it into the past via the ORM.
        past = timezone.now() - timedelta(minutes=16)
        PasswordResetToken.objects.filter(pk=token.pk).update(created_at=past)
        token.refresh_from_db()

        self.assertTrue(token.is_expired())
        self.assertFalse(token.is_valid())

    def test_token_just_under_15_minutes_is_still_valid(self):
        token = PasswordResetToken.objects.create(
            email='alice@example.com',
            token=PasswordResetToken.generate_token(),
        )
        recent = timezone.now() - timedelta(minutes=14)
        PasswordResetToken.objects.filter(pk=token.pk).update(created_at=recent)
        token.refresh_from_db()

        self.assertFalse(token.is_expired())
        self.assertTrue(token.is_valid())

    def test_used_token_is_invalid_even_when_not_expired(self):
        token = PasswordResetToken.objects.create(
            email='alice@example.com',
            token=PasswordResetToken.generate_token(),
            is_used=True,
        )

        self.assertFalse(token.is_expired())
        self.assertFalse(token.is_valid())

    def test_generate_token_returns_unique_values(self):
        tokens = {PasswordResetToken.generate_token() for _ in range(100)}
        self.assertEqual(len(tokens), 100)
