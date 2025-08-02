from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from loguru import logger


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider_id, error, exception, extra_context):
        """
        Handle authentication errors with secure logging that doesn't expose sensitive data
        """
        # Log sanitized error information without sensitive request data
        sanitized_error_data = {
            "provider_id": str(provider_id),
            "error_type": type(error).__name__,
            "exception_type": type(exception).__name__,
            "has_extra_context": bool(extra_context),
        }
        logger.error("SocialAccount authentication error!")
        logger.error(sanitized_error_data)

        # Additional debugging for SAML (without sensitive data)
        if hasattr(provider_id, "id") and provider_id.id == "saml":
            logger.error("SAML Error Details:")
            logger.error(f"Request method: {request.method}")
            # Log only the presence of data, not the actual data
            logger.error(f"Has POST data: {bool(request.POST)}")
            logger.error(f"Has GET data: {bool(request.GET)}")

            # Log SAML-specific errors (these are not sensitive)
            saml_errors = extra_context.get("saml_errors", [])
            saml_last_error_reason = extra_context.get("saml_last_error_reason", "")
            logger.error(f"SAML Error count: {len(saml_errors)}")
            logger.error(f"SAML Last Error Reason available: {bool(saml_last_error_reason)}")

    def pre_social_login(self, request, sociallogin):
        """Called before a social login is processed."""
        logger.debug(f"Pre-social login for provider: {sociallogin.account.provider}")
        logger.debug(f"Social account UID: {sociallogin.account.uid}")
        logger.debug(f"Social account extra data: {sociallogin.account.extra_data}")

    def save_user(self, request, sociallogin, form=None):
        """Called when saving a new user from social login."""
        logger.debug(f"Saving user from social login: {sociallogin.account.provider}")
        return super().save_user(request, sociallogin, form)

    def populate_user(self, request, sociallogin, data):
        """Called to populate user fields from social account data."""
        logger.debug(f"Populating user data from provider: {sociallogin.account.provider}")
        # Log data keys only, not values to avoid logging sensitive information
        logger.debug(f"Available data keys: {list(data.keys()) if data else 'None'}")
        return super().populate_user(request, sociallogin, data)
