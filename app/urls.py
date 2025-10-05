# app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CityWeatherView,
    LocationViewSet, 
    DailyForecastViewSet, 
    HourlyForecastViewSet, 
    WeatherAlertViewSet, 
    FavoriteLocationViewSet,
    CurrentWeatherView
)

# Creamos un Router para manejar automáticamente las rutas ViewSet
router = DefaultRouter()

# Registrar ViewSets para CRUD completo
router.register(r'locaciones', LocationViewSet)
router.register(r'pronosticos-diarios', DailyForecastViewSet)
router.register(r'pronosticos-horarios', HourlyForecastViewSet)
router.register(r'alertas', WeatherAlertViewSet)
router.register(r'favoritos', FavoriteLocationViewSet) # Rutas para favoritos (POST, GET, DELETE)

urlpatterns = [
     path('clima-actual/', CurrentWeatherView.as_view(), name='clima-actual'), # Ruta para clima actual
     path('clima-por-ciudad/', CityWeatherView.as_view(), name='city-weather'),
    # Incluye todas las rutas generadas por el router (ej: /locaciones/, /locaciones/1/, etc.)
    path('', include(router.urls)),
]