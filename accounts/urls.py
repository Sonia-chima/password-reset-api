from django.urls import path

from .views import PasswordResetRequestView, PasswordResetConfirmView

# Dedicated URLconf for the password-reset feature.
urlpatterns = [
    path(
        'password-reset-request',
        PasswordResetRequestView.as_view(),
        name='password-reset-request',
    ),
    path(
        'password-reset-confirm',
        PasswordResetConfirmView.as_view(),
        name='password-reset-confirm',
    ),
]
