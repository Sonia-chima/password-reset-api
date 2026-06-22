from django.urls import path

from .views import PasswordResetRequestView

# Dedicated URLconf for the password-reset feature.
urlpatterns = [
    path(
        'password-reset-request',
        PasswordResetRequestView.as_view(),
        name='password-reset-request',
    ),
]
