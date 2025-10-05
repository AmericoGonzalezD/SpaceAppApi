# app/serializers.py

from rest_framework import serializers
from .models import (
    Location, 
    DailyForecast, 
    HourlyForecast, 
    WeatherAlert, 
    FavoriteLocation
)
from django.contrib.auth import get_user_model

User = get_user_model()


# Serializers Anidados (Detalles)
# ----------------------------------------------------------------------

class HourlyForecastSerializer(serializers.ModelSerializer):
    """Serializa los datos de pronóstico por hora."""
    class Meta:
        model = HourlyForecast
        fields = ['time', 'temperature', 'condition', 'precipitation_perc']
        
class WeatherAlertSerializer(serializers.ModelSerializer):
    """Serializa las alertas de clima."""
    class Meta:
        model = WeatherAlert
        fields = ['type', 'start_time', 'date', 'details', 'probability']


# Serializer Principal (Home Screen)
# ----------------------------------------------------------------------

class DailyForecastSerializer(serializers.ModelSerializer):
    """Serializa el pronóstico diario e incluye sus detalles por hora y alertas."""
    # Usamos los related_name definidos en los modelos (hourly_forecasts, alerts)
    hourly_forecasts = HourlyForecastSerializer(many=True, read_only=True)
    alerts = WeatherAlertSerializer(many=True, read_only=True)

    class Meta:
        model = DailyForecast
        # Usamos '__all__' ya que todos los campos son relevantes para la Home/Details Screen
        fields = '__all__' 


# Serializers de Base
# ----------------------------------------------------------------------

class LocationSerializer(serializers.ModelSerializer):
    """Serializa la información geográfica de una ubicación."""
    
    # Opcional: Podrías incluir el pronóstico actual o de hoy aquí
    
    class Meta:
        model = Location
        fields = '__all__'

class FavoriteLocationSerializer(serializers.ModelSerializer):
    """Serializa la relación de favoritos, incluyendo la data de la ubicación."""
    
    # Muestra los detalles completos de la ubicación en lugar solo del ID
    location_details = LocationSerializer(source='location', read_only=True)
    
    class Meta:
        model = FavoriteLocation
        # Excluimos 'user' para la entrada (será asignado en la vista)
        fields = ['id', 'location', 'location_details', 'user']
        read_only_fields = ['user']