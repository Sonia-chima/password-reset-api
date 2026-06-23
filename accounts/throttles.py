from rest_framework.throttling import SimpleRateThrottle


class PasswordResetRequestThrottle(SimpleRateThrottle):
    """Throttle password-reset requests per client IP.

    The rate is configured in settings under DEFAULT_THROTTLE_RATES via this
    scope (currently 5 requests/hour). Keying is always done by IP address so
    the limit applies regardless of authentication state.
    """

    scope = 'password_reset_request'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }
