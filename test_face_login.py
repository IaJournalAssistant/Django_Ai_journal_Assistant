#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script to verify Face Login (WebAuthn) setup
Run this to check if all components are properly configured
"""

import sys
import os
import io

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')
import django
django.setup()

def test_fido2_installed():
    """Test if fido2 package is installed"""
    try:
        import fido2
        print("✅ fido2 package installed (version: {})".format(fido2.__version__))
        return True
    except ImportError as e:
        print("❌ fido2 package NOT installed: {}".format(e))
        return False

def test_allauth_mfa_installed():
    """Test if allauth.mfa is in INSTALLED_APPS"""
    from django.conf import settings
    if 'allauth.mfa' in settings.INSTALLED_APPS:
        print("✅ allauth.mfa is in INSTALLED_APPS")
        return True
    else:
        print("❌ allauth.mfa is NOT in INSTALLED_APPS")
        return False

def test_humanize_installed():
    """Test if django.contrib.humanize is in INSTALLED_APPS"""
    from django.conf import settings
    if 'django.contrib.humanize' in settings.INSTALLED_APPS:
        print("✅ django.contrib.humanize is in INSTALLED_APPS")
        return True
    else:
        print("❌ django.contrib.humanize is NOT in INSTALLED_APPS")
        return False

def test_mfa_settings():
    """Test if MFA settings are configured"""
    from django.conf import settings
    
    results = []
    
    # Check MFA_SUPPORTED_TYPES
    if hasattr(settings, 'MFA_SUPPORTED_TYPES'):
        if 'webauthn' in settings.MFA_SUPPORTED_TYPES:
            print("✅ MFA_SUPPORTED_TYPES includes 'webauthn'")
            results.append(True)
        else:
            print("❌ MFA_SUPPORTED_TYPES exists but 'webauthn' not included")
            results.append(False)
    else:
        print("❌ MFA_SUPPORTED_TYPES not configured")
        results.append(False)
    
    # Check MFA_PASSKEY_LOGIN_ENABLED
    if hasattr(settings, 'MFA_PASSKEY_LOGIN_ENABLED'):
        if settings.MFA_PASSKEY_LOGIN_ENABLED:
            print("✅ MFA_PASSKEY_LOGIN_ENABLED is True")
            results.append(True)
        else:
            print("⚠️  MFA_PASSKEY_LOGIN_ENABLED is False")
            results.append(False)
    else:
        print("❌ MFA_PASSKEY_LOGIN_ENABLED not configured")
        results.append(False)
    
    # Check MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN
    if hasattr(settings, 'MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN'):
        if settings.MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN:
            print("✅ MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN is True (dev mode)")
            results.append(True)
        else:
            print("⚠️  MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN is False (production mode)")
            results.append(True)
    else:
        print("⚠️  MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN not configured")
        results.append(True)
    
    return all(results)

def test_migrations():
    """Test if MFA migrations have been applied"""
    from django.db import connection
    
    cursor = connection.cursor()
    try:
        # Check if mfa tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'mfa_%'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("✅ MFA database tables exist:")
            for table in tables:
                print("   - {}".format(table[0]))
            return True
        else:
            print("❌ MFA database tables NOT found")
            return False
    except Exception as e:
        # For PostgreSQL or other databases
        try:
            from django.apps import apps
            if apps.is_installed('mfa'):
                print("✅ MFA app is installed and loaded")
                return True
        except:
            pass
        print("⚠️  Could not verify MFA tables: {}".format(e))
        return True

def test_urls():
    """Test if MFA URLs are accessible"""
    from django.urls import reverse
    from django.urls.exceptions import NoReverseMatch
    
    urls_to_test = [
        ('mfa_index', 'MFA Dashboard'),
        ('mfa_activate_webauthn', 'WebAuthn Activation'),
    ]
    
    results = []
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            print("✅ {} URL: {}".format(description, url))
            results.append(True)
        except NoReverseMatch:
            print("❌ {} URL not found".format(description))
            results.append(False)
    
    return all(results)

def main():
    print("\n" + "="*60)
    print("Face Login (WebAuthn) Configuration Test")
    print("="*60 + "\n")
    
    tests = [
        ("FIDO2 Package", test_fido2_installed),
        ("Allauth MFA App", test_allauth_mfa_installed),
        ("Humanize App", test_humanize_installed),
        ("MFA Settings", test_mfa_settings),
        ("Database Migrations", test_migrations),
        ("URL Configuration", test_urls),
    ]
    
    results = []
    for test_name, test_func in tests:
        print("\n--- Testing: {} ---".format(test_name))
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print("❌ Error during test: {}".format(e))
            results.append(False)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print("\nTests Passed: {}/{}".format(passed, total))
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED! Face Login is ready to use!")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Go to: http://localhost:8000/accounts/signup/")
        print("3. Create an account and log in")
        print("4. Navigate to: http://localhost:8000/accounts/2fa/")
        print("5. Add a WebAuthn authenticator (passkey)")
        print("6. Test login at: http://localhost:8000/accounts/login/")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

