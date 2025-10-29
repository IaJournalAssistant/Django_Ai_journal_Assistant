# Face Login (Passkeys/WebAuthn) Setup Guide

## ✅ What Has Been Installed

Your Django app now supports **Face Login** using **WebAuthn/Passkeys**, which includes:

- Face ID (iOS/macOS Safari)
- Windows Hello (Windows Edge/Chrome)
- Touch ID (macOS Safari/Chrome)
- Android biometric authentication
- Hardware security keys (YubiKey, etc.)

## 🔧 How It Works

1. **No biometric data is stored on your server** - only public keys
2. Users register a passkey once (after creating an account)
3. They can then sign in using Face ID/Windows Hello without a password
4. Passwords remain available as a fallback method

## 📋 Setup Steps

### Step 1: Start the Development Server

The server should already be running. If not:

```bash
.\venv\Scripts\activate
python manage.py runserver
```

### Step 2: Create a Test Account

1. Go to `http://localhost:8000/accounts/signup/`
2. Create a new account with username/email/password
3. Complete the signup process

### Step 3: Register a Passkey

1. After logging in, navigate to: `http://localhost:8000/accounts/2fa/`
2. Click **"Activate Authenticators"** or **"Add Authenticator"**
3. Choose **"Security Key (WebAuthn)"**
4. Follow the browser prompts:
   - **Windows**: Windows Hello (PIN, fingerprint, or face)
   - **Mac**: Touch ID or Face ID
   - **Mobile**: Face/fingerprint unlock
5. Give your passkey a name (e.g., "My Laptop", "iPhone Face ID")
6. Click **"Add"**

### Step 4: Test Passkey Login

1. Log out: `http://localhost:8000/accounts/logout/`
2. Go to login page: `http://localhost:8000/accounts/login/`
3. You should see a **"Sign in with Face ID / Passkey"** button
4. Click it and authenticate with your biometric

## 🎨 UI Elements Added

### Login Page (`templates/account/login.html`)

- **Passkey button**: Green gradient button with lock icon
- Only appears when `MFA_PASSKEY_LOGIN_ENABLED = True`
- Uses allauth's `login_by_passkey_url` endpoint

### Signup Page (`templates/account/signup.html`)

- Already had a passkey slot - now active!
- Users can register a passkey during signup (optional)

## ⚙️ Settings Configured

In `a_core/settings.py`:

```python
# Added to INSTALLED_APPS
'django.contrib.humanize',
'allauth.mfa',

# WebAuthn/Passkey Settings
MFA_SUPPORTED_TYPES = ["totp", "webauthn", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True  # ⚠️ Dev only!
```

## 🔒 Security Notes

### For Development (HTTP localhost)

- `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True` allows testing on `http://localhost`
- This is **only for development** and must be removed in production

### For Production (HTTPS required)

When deploying to production:

1. **Remove** the insecure origin setting:

```python
# Delete or set to False:
# MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True
```

2. **Ensure HTTPS** is configured:

   - WebAuthn requires HTTPS in production
   - Use a proper SSL certificate
   - Configure your web server (nginx, Apache, etc.)

3. **Test thoroughly**:
   - Register passkeys on production domain
   - Test on multiple devices/browsers

## 🌐 Browser Compatibility

| Browser | Platform | Biometric Support            |
| ------- | -------- | ---------------------------- |
| Safari  | macOS    | Touch ID, Face ID            |
| Safari  | iOS      | Face ID, Touch ID            |
| Chrome  | Windows  | Windows Hello                |
| Edge    | Windows  | Windows Hello                |
| Chrome  | macOS    | Touch ID                     |
| Chrome  | Android  | Fingerprint, Face Unlock     |
| Firefox | All      | Security Keys, Platform Auth |

## 🛠️ Troubleshooting

### "Sign in with Passkey" button doesn't appear

- Check that `MFA_PASSKEY_LOGIN_ENABLED = True` in settings
- Restart the development server
- Clear browser cache

### "Passkey registration failed"

- Ensure you're on `http://localhost` (not 127.0.0.1)
- Check that `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True`
- Try a different browser
- Check browser console for errors

### Can't find the registration page

- Go to: `http://localhost:8000/accounts/2fa/`
- Or navigate from account settings (if you've added a link)

### Production deployment issues

- Verify HTTPS is working
- Remove `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN`
- Check browser console for HTTPS-related errors
- Test on the actual production domain (not IP address)

## 📱 Adding Links to Your UI

You can add links to the MFA management page in your profile/settings:

```html
<a href="{% url 'mfa_index' %}">Manage Security & Passkeys</a>
```

Or specific actions:

```html
<!-- Add a new passkey -->
<a href="{% url 'mfa_activate_webauthn' %}">Add Face ID / Security Key</a>

<!-- View all authenticators -->
<a href="{% url 'mfa_list_authenticators' %}">Manage Authenticators</a>
```

## 🎯 Next Steps

1. **Test the feature** on localhost with your device's biometrics
2. **Add navigation links** to help users find the passkey registration
3. **Update your onboarding flow** to encourage passkey setup
4. **Deploy to production** with HTTPS and proper security settings
5. **Monitor usage** to see how many users adopt passwordless login

## 📦 Dependencies Installed

- `fido2` - WebAuthn/FIDO2 protocol implementation
- `cryptography` - Cryptographic operations for WebAuthn
- `cffi` - C Foreign Function Interface (required by cryptography)

All added to `requirements.txt` for deployment.

## 🔗 Useful URLs

- MFA Dashboard: `http://localhost:8000/accounts/2fa/`
- Add WebAuthn: `http://localhost:8000/accounts/2fa/webauthn/activate/`
- Login Page: `http://localhost:8000/accounts/login/`
- Signup Page: `http://localhost:8000/accounts/signup/`

---

**Need help?** Check the django-allauth documentation:

- [WebAuthn Documentation](https://docs.allauth.org/en/dev/mfa/webauthn.html)
- [MFA Overview](https://docs.allauth.org/en/dev/mfa/)
