# app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocationViewSet, 
    DailyForecastViewSet, 
    HourlyForecastViewSet, 
    WeatherAlertViewSet, 
    FavoriteLocationViewSet
)

# Creamos un Router para manejar automáticamente las rutas ViewSet
router = DefaultRouter()

# Registrar ViewSets para CRUD completo
router.register(r'locations', LocationViewSet)
router.register(r'daily-forecasts', DailyForecastViewSet)
router.register(r'hourly-forecasts', HourlyForecastViewSet)
router.register(r'alerts', WeatherAlertViewSet)
router.register(r'favorites', FavoriteLocationViewSet) # Rutas para favoritos (POST, GET, DELETE)

urlpatterns = [
    # Incluye todas las rutas generadas por el router (ej: /locations/, /locations/1/, etc.)
    path('', include(router.urls)),
]