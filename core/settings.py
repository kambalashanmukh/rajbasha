from pathlib import Path
import os
<<<<<<< Updated upstream
from decouple import config
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
  return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")

=======

BASE_DIR = Path(__file__).resolve().parent.parent
>>>>>>> Stashed changes

# SECURITY
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ymob%9c8jb8=ld@^f(*(sc-)m7i=zgvcn6c+k85l7s5m@&hce(')
DEBUG = True
<<<<<<< Updated upstream

# Keep this False while testing on HTTP.
# Set DJANGO_USE_HTTPS_SECURITY=true only when running behind HTTPS.
USE_HTTPS_SECURITY = env_bool("DJANGO_USE_HTTPS_SECURITY", False)

"""SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000")) if USE_HTTPS_SECURITY else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS_SECURITY
SECURE_HSTS_PRELOAD = USE_HTTPS_SECURITY"""

ALLOWED_HOSTS = ["10.160.19.20", "192.168.56.101", "127.0.0.1", "localhost","192.168.1.8"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # Forces HTTPS for 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
=======
SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 2. Allow local host (Required when DEBUG is False)
ALLOWED_HOSTS = ['*']


>>>>>>> Stashed changes
# APPLICATIONS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'django_bootstrap5',
    'rest_framework',
    'captcha',

    # Your Apps
    # 'user',
    'website',
    
]


# MIDDLEWARE
MIDDLEWARE = [
<<<<<<< Updated upstream
  "django.middleware.security.SecurityMiddleware",
  "whitenoise.middleware.WhiteNoiseMiddleware",
  "website.middleware.SecurityHeadersMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
=======
    'django.middleware.security.SecurityMiddleware',
    'website.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # # Custom middleware should always be last
    # 'website.middleware.DynamicTranslationMiddleware',
>>>>>>> Stashed changes
]


ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

CSRF_TRUSTED_ORIGINS = [
<<<<<<< Updated upstream
  "http://192.168.1.8:8000"
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  "http://10.160.19.20:8000",
  "http://192.168.56.101:8000",
=======
    'http://127.0.0.1:8000',
    'http://localhost:8000'
>>>>>>> Stashed changes
]

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Your custom context processor
                'website.context_processors.global_settings',
            ],
        },
    },
]


# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}


# PASSWORD VALIDATION (Combined both)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True


# STATIC FILES
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# AUTH SETTINGS
AUTH_USER_MODEL = 'website.CustomUser'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'petertriffle@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'eetekzvolwnphbqf')


# CSRF / SECURITY
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000'
]

<<<<<<< Updated upstream
#CSRF_COOKIE_SECURE = USE_HTTPS_SECURITY
#SESSION_COOKIE_SECURE = USE_HTTPS_SECURITY

# Keep False if your JS reads csrftoken from cookie.
#CSRF_COOKIE_HTTPONLY = False
#SESSION_COOKIE_HTTPONLY = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
=======
CSRF_FAILURE_VIEW = 'website.views.csrf_failure'
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
>>>>>>> Stashed changes


# CACHE (Keeping your DB cache instead of locmem)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, '.django_cache'),
    }
}

'''CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_translation_cache',
    }
}'''


# CAPTCHA
CAPTCHA_IMAGE_SIZE = (160, 60)
CAPTCHA_FONT_SIZE = 32
CAPTCHA_FOREGROUND_COLOR = '#000000' # Black text
CAPTCHA_LETTER_ROTATION = (-15, 15)
CAPTCHA_LENGTH = 5
CAPTCHA_NOISE_FUNCTIONS = (
    'captcha.helpers.noise_arcs', # Adds those curved lines
    'captcha.helpers.noise_dots', # Adds the grainy background
)
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.random_char_challenge'
CAPTCHA_FLITE_PATH = os.path.join(BASE_DIR, 'espeak_wrapper.sh')

# ENCRYPTION
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'EOxZWt1RC6O9GKhF8d30FUxyCyjGAz29smC5i8tWA0I=')
<<<<<<< Updated upstream

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

X_FRAME_OPTIONS = 'DENY'
=======
CSRF_FAILURE_VIEW = 'website.views.csrf_failure'


MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000 
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
>>>>>>> Stashed changes
