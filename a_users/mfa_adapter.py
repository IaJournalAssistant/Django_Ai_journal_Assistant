"""
Custom MFA Adapter to bypass email verification requirement for development
"""
from allauth.mfa.adapter import DefaultMFAAdapter


class NoEmailVerificationMFAAdapter(DefaultMFAAdapter):
    """
    Custom MFA adapter that doesn't require email verification.
    
    This is useful for development/testing purposes where you want to enable
    passkeys/2FA without requiring users to verify their email first.
    
    WARNING: In production, you should use the default adapter which DOES
    require email verification for security reasons.
    """
    
    def validate_can_add_authenticator(self, user):
        """
        Override to skip email verification check.
        
        The default implementation checks if the user has verified their email
        to prevent attackers from locking out account owners. For development,
        we skip this check.
        """
        # In development, allow MFA setup without email verification
        # In production, you should remove this override
        pass

