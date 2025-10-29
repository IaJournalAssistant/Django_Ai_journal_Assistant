# Django AI Journal Assistant

A smart journaling application with AI-powered features and Face Login authentication.

## 🆕 New Features

### 🔐 Face Login (WebAuthn/Passkeys)

- Sign in with Face ID (iOS/macOS)
- Sign in with Windows Hello (Windows)
- Sign in with Touch ID (macOS)
- Hardware security key support
- **No passwords needed!**

**Quick Start**: See [QUICK_START.md](QUICK_START.md) for setup instructions.

## 📦 Packages

| Package               | Version |
| --------------------- | ------- |
| Django                | 5.2.4   |
| django-allauth        | 65.9.0  |
| django-browser-reload | 1.18.0  |
| django-cleanup        | 9.0.0   |
| django-htmx           | 1.23.2  |
| pillow                | 11.3.0  |
| djangorestframework   | 3.15.2  |
| psycopg[binary]       | latest  |
| fido2                 | 2.0.0   |

## 🚀 Getting Started

#### Getting the files

Download zip file or use git clone:

```bash
git clone https://github.com/andyjud/django-starter.git . && rm -rf .git
```

## 📥 Setup

### 1. Create Virtual Environment

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Database

Update `a_core/settings.py` with your PostgreSQL credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'DjangoProject',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Migrate database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run application

```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

## 🔐 Face Login Setup

After setting up the application:

1. **Create an account**: http://localhost:8000/accounts/signup/
2. **Register a passkey**: http://localhost:8000/accounts/2fa/
3. **Test Face Login**: http://localhost:8000/accounts/login/

See [QUICK_START.md](QUICK_START.md) for detailed instructions.

## 📚 Documentation

- **QUICK_START.md** - Face Login quick setup guide
- **FACE_LOGIN_GUIDE.md** - Comprehensive Face Login documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details
- **DESIGN_UPDATES.md** - UI/UX design documentation

## 🔒 Security

### Development

The app is currently configured for development with:

- DEBUG = True
- HTTP support for WebAuthn (localhost only)
- Console email backend

### Production Checklist

Before deploying to production:

- [ ] Generate and set a new SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Remove `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN`
- [ ] Enable HTTPS
- [ ] Configure production email backend
- [ ] Use environment variables for sensitive data

#### Generate Secret Key

```bash
python manage.py shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
exit()
```

## 🌟 Features

- ✅ User authentication (username/email + password)
- ✅ **Face Login / Passkeys** (WebAuthn)
- ✅ Journal entries with rich text
- ✅ Media file management
- ✅ RESTful API with token authentication
- ✅ Responsive modern UI with Tailwind CSS
- ✅ HTMX for dynamic interactions
- 🔜 AI-powered insights (coming soon)

## 🛠️ Tech Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL
- **Authentication**: django-allauth + WebAuthn
- **API**: Django REST Framework
- **Frontend**: Tailwind CSS, Alpine.js, HTMX
- **Security**: WebAuthn/FIDO2 for biometric authentication

## 🔧 Troubleshooting

### Face Login Issues

See [FACE_LOGIN_GUIDE.md](FACE_LOGIN_GUIDE.md) for troubleshooting.

### Database Connection Issues

- Verify PostgreSQL is running
- Check database credentials in settings.py
- Ensure database exists: `createdb DjangoProject`

### Static Files Not Loading

```bash
python manage.py collectstatic
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🎥 Video Tutorial

https://youtu.be/SQ4A7Q6_md8

---

**Last Updated**: October 29, 2025  
**Status**: Active Development  
**New Feature**: Face Login ✨
