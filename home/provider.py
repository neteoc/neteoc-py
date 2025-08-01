from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from loguru import logger


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider_id, error, exception, extra_context):
        extra_data = {
            "provider_id": provider_id,
            "error": error.__str__(),
            "exception": exception.__str__(),
            "extra_context": extra_context,
        }
        logger.error("SocialAccount authentication error!")
        logger.error(extra_data)

        # Additional debugging for SAML
        if hasattr(provider_id, "id") and provider_id.id == "saml":
            logger.error("SAML Error Details:")
            logger.error(f"Request method: {request.method}")
            logger.error(f"Request POST data: {dict(request.POST)}")
            logger.error(f"Request GET data: {dict(request.GET)}")

            # Log SAML-specific errors
            saml_errors = extra_context.get("saml_errors", [])
            saml_last_error_reason = extra_context.get("saml_last_error_reason", "")
            logger.error(f"SAML Errors: {saml_errors}")
            logger.error(f"SAML Last Error Reason: {saml_last_error_reason}")

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
        logger.debug(f"Available data: {data}")
        return super().populate_user(request, sociallogin, data)
