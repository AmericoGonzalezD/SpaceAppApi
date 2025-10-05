"""
Django settings for config project.
"""
import os
from pathlib import Path
import environ # Necesario si usas variables de entorno para la BD

# Inicializa django-environ (si lo usas)
env = environ.Env(
    # Define tipos de datos si es necesario
    DEBUG=(bool, False) 
)

# Configura la búsqueda de archivos .env
# Lee el archivo .env si existe (usado en local)
environ.Env.read_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR apunta a la raíz del proyecto (SPACEAPPAPI)
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-s5u57%iuyvpq9+@p_$(5q$vc8b^dbid^4ei64ssff8-z!qijxj')

# SECURITY WARNING: don't run with debug turned on in production!
# Usa False en producción y True solo para depurar en local.
DEBUG = env('DEBUG', default=False) 

# Lista de hosts permitidos (corregidos para evitar errores DisallowedHost)
ALLOWED_HOSTS = [
    # Dominio personalizado
    'weatheron.earth', 
    'www.weatheron.earth',
    # Dominio de Azure App Service (reemplaza 'tu-app' por el nombre real)
    '.azurewebsites.net', 
    # Hosts internos de Azure y local (para depuración y verificación de salud)
    '127.0.0.1',
    '169.254.131.4', 
    '169.254.131.5',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'app', # Tu aplicación principal
]

MIDDLEWARE = [
    # ... (Middleware estándar) ...
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ... (Configuración de TEMPLATES) ...

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------
# DATABASE CONFIGURATION
# ---------------------------
# Si usas django-environ con URL:
# DATABASES = {'default': env.db()}

# Si usas configuración manual (debe coincidir con la desactivación SSL en Azure Portal):
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', default='dbspaceapp'),
        'USER': env('DB_USER', default='myadmin'),
        'PASSWORD': env('DB_PASSWORD', default='Prueba10'),
        'HOST': env('DB_HOST', default='spaceapp.mysql.database.azure.com'),
        'PORT': env('DB_PORT', default='3306'),
        
        # Corrección Final para SSL: 
        # Si require_secure_transport está en OFF en Azure MySQL, OPTIONS debe estar vacío 
        # o explícitamente configurado para NO usar SSL.
        'OPTIONS': {
            # Descomenta esta línea SÓLO si el error 2026 persiste y tu servidor lo permite:
            # 'ssl': False, 
        }
    }
}
# ---------------------------


# ... (Configuración de validación de contraseña) ...


# Configuración de CSRF (Corregido)
CSRF_TRUSTED_ORIGINS = [
    'https://weatheron.earth',
    'https://www.weatheron.earth',
    'https://' + env('WEBSITE_HOSTNAME', default=''), # Agrega el dominio de Azure
]


# ---------------------------
# STATIC FILES (Estilos Admin)
# ---------------------------
# STATIC_ROOT es la ubicación donde collectstatic reunirá todos los archivos.
# Debe apuntar a la raíz del proyecto para que Azure App Service los sirva.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATIC_URL es la URL base para acceder a los archivos estáticos.
STATIC_URL = '/static/' 
# ---------------------------


# Internationalization (mantenido)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración adicional de seguridad (Recomendado cuando DEBUG=False)
if not DEBUG:
    # Fuerza HTTPS para todas las cookies de sesión
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000 # Un año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True