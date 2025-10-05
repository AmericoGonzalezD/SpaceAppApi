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
router.register(r'locaciones', LocationViewSet)
router.register(r'pronosticos-diarios', DailyForecastViewSet)
router.register(r'pronosticos-horarios', HourlyForecastViewSet)
router.register(r'alertas', WeatherAlertViewSet)
router.register(r'favoritos', FavoriteLocationViewSet) # Rutas para favoritos (POST, GET, DELETE)

urlpatterns = [
    # Incluye todas las rutas generadas por el router (ej: /locaciones/, /locaciones/1/, etc.)
    path('', include(router.urls)),
]