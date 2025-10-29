# How to Test Face Login / Passkey Feature

## Important: You MUST Register a Passkey First!

The "Sign in with Face ID / Passkey" button only works if you've already registered a passkey for your account. Here's the correct order:

## Step-by-Step Testing Guide

### Step 1: Create an Account or Login
1. Go to http://localhost:8000/accounts/signup/ (or login if you have an account)
2. Create an account with username and password
3. Complete signup

### Step 2: Register a Passkey (REQUIRED)
1. After logging in, go to: **http://localhost:8000/accounts/2fa/**
2. You should see a page for managing authenticators
3. Look for a button like "Add authenticator" or "Add security key"
4. Click it and select "WebAuthn" or "Security Key"
5. Your browser will prompt you:
   - **Windows**: Windows Hello (PIN, fingerprint, or face camera)
   - **Mac**: Touch ID or Face ID prompt
   - **Mobile**: Fingerprint or face unlock
6. Follow the prompts and give your passkey a name (e.g., "My Laptop")
7. Click save/add

### Step 3: Test Passkey Login
1. **Log out**: http://localhost:8000/accounts/logout/
2. **Go to login page**: http://localhost:8000/accounts/login/
3. **You should see the green "Sign in with Face ID / Passkey" button**
4. **Click it**
5. Your browser will prompt for authentication
6. Authenticate with your biometric
7. You should be logged in!

## Troubleshooting

### Button doesn't do anything when clicked
**Likely causes:**
- You haven't registered a passkey yet (see Step 2 above)
- JavaScript not loading properly (check browser console)
- No passkeys registered for this account

### "This account has no passkeys" or similar error
- You need to register a passkey first (Step 2)
- Make sure you're logged into the correct account

### Browser doesn't show biometric prompt
- Make sure you're on `http://localhost` (not 127.0.0.1)
- Try a different browser (Chrome/Edge recommended)
- Check if your device supports WebAuthn
- Look for browser errors in the console (F12)

### Email verification error when adding passkey
- Make sure the server has restarted after the latest changes
- The monkey-patch in `a_users/apps.py` should bypass this

## Testing Checklist

- [ ] Account created and logged in
- [ ] Navigated to http://localhost:8000/accounts/2fa/
- [ ] Successfully added a WebAuthn/passkey
- [ ] Logged out
- [ ] Clicked "Sign in with Face ID / Passkey" button
- [ ] Browser showed biometric prompt
- [ ] Successfully logged in with passkey

## Quick Test URLs

- **Signup**: http://localhost:8000/accounts/signup/
- **Login**: http://localhost:8000/accounts/login/
- **MFA/Passkey Setup**: http://localhost:8000/accounts/2fa/
- **Profile Settings**: http://localhost:8000/profile/ (has link to MFA)
- **Logout**: http://localhost:8000/accounts/logout/

## Expected Flow

```
1. Signup → 2. Login → 3. Add Passkey (/accounts/2fa/) → 4. Logout → 5. Login with Passkey
```

**IMPORTANT**: Steps 1-3 must be completed before step 5 will work!

