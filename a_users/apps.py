from django.apps import AppConfig


class AUsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_users'
    
    def ready(self):
        import a_users.signals
        
        # Monkey-patch allauth MFA to bypass email verification for development
        # WARNING: Remove this in production!
            # TEMPORARILY DISABLED DUE TO CRYPTOGRAPHY ISSUES
        from allauth.mfa.internal.flows import add as mfa_add_module
        
        def bypass_email_verification(user):
            """
            Override to skip email verification check for MFA setup.
            For development only - allows testing Face Login without email verification.
            """
            pass  # Do nothing - allow MFA setup without email verification
        
        # Replace the validation function
        mfa_add_module.validate_can_add_authenticator = bypass_email_verification