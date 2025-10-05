# app/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User # Necesario para FavoriteLocation
from datetime import time

# Configuración de precisión para los nuevos campos científicos
# Usamos 12 dígitos en total, 6 después del punto decimal.
DECIMAL_PRECISION = 12
DECIMAL_PLACES = 6

# ==============================================================================
# 1. Modelo Location (Ubicación)
# ==============================================================================

class Location(models.Model):
    """Representa una ubicación geográfica cuya información climática se rastrea."""
    
    # Datos de identificación de la ubicación
    city = models.CharField(max_length=100, help_text="Ej: Monterrey")
    state_province = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: N.L. / Esp")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Mexico / Esp")
    
    # Coordenadas geográficas
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.city}, {self.state_province}"

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        unique_together = ('latitude', 'longitude')

# ==============================================================================
# 2. Modelo DailyForecast (Pronóstico Diario)
# ==============================================================================

class DailyForecast(models.Model):
    """Almacena el pronóstico general del clima para un día específico en una Location."""

    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='daily_forecasts')
    date = models.DateField(default=timezone.now)

    # --- Campos de la UI (Pantalla Principal) ---
    current_temp = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperatura actual")
    condition_summary = models.CharField(max_length=100, help_text="Ej: Partly cloudy")
    max_temp = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperatura máxima")
    min_temp = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperatura mínima")
    feels_like_temp = models.DecimalField(max_digits=4, decimal_places=1, help_text="Sensación térmica")

    # --- Datos de Detalles ---
    humidity = models.IntegerField(help_text="Humedad en %")
    precipitation_prob = models.IntegerField(help_text="Probabilidad de lluvia en %")
    wind_speed = models.DecimalField(max_digits=4, decimal_places=1, help_text="Velocidad del viento")
    wind_direction = models.CharField(max_length=10, help_text="Ej: WSW")
    visibility = models.DecimalField(max_digits=4, decimal_places=1, help_text="Visibilidad")
    pressure = models.DecimalField(max_digits=7, decimal_places=2, help_text="Presión Atmosférica") # Corregido a 7

    uv_index = models.CharField(max_length=50, default="Low 0")
    air_quality = models.CharField(max_length=50, default="Low 0")
    dew_point = models.DecimalField(max_digits=4, decimal_places=1, help_text="Punto de rocío")
    clouds = models.DecimalField(max_digits=4, decimal_places=1, help_text="Nubosidad")

    # Sol y Luna
    sunrise = models.TimeField(default=time(6, 0)) # Añadimos default para el script de ML
    sunset = models.TimeField(default=time(18, 0)) # Añadimos default para el script de ML
    summary = models.TextField(blank=True, null=True, help_text="Resumen del día")
    
    # ----------------------------------------------------------------------
    # Nuevos Campos: Variables Físicas del Modelo Predictivo
    # ----------------------------------------------------------------------
    CO_surface_conc = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    total_precip_rate = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    specific_humidity_pred = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    temperature_surface = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    skin_temperature = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    avg_wind_speed_10m = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    surface_pressure_pred = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    cloud_area_pred = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    frozen_precip = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    snowfall_pred = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    dust_concentration = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    SO2_concentration = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    NO2_concentration = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    O3_concentration = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    potential_vorticity = models.DecimalField(max_digits=DECIMAL_PRECISION, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    # ----------------------------------------------------------------------

    def __str__(self):
        return f"{self.location.city} - {self.date}"

    class Meta:
        verbose_name = "Pronóstico Diario"
        verbose_name_plural = "Pronósticos Diarios"
        unique_together = ('location', 'date')

# ==============================================================================
# 3. Modelo HourlyForecast (Pronóstico por Hora)
# ==============================================================================

class HourlyForecast(models.Model):
    """Almacena el pronóstico del clima para una hora específica dentro de un DailyForecast."""

    daily_forecast = models.ForeignKey(DailyForecast, on_delete=models.CASCADE, related_name='hourly_forecasts')
    time = models.TimeField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    condition = models.CharField(max_length=100, help_text="Ej: Partly cloudy")
    precipitation_perc = models.IntegerField(help_text="Precipitación en %")

    def __str__(self):
        return f"{self.daily_forecast.location.city} - {self.daily_forecast.date} @ {self.time.strftime('%H:%M')}"

    class Meta:
        verbose_name = "Pronóstico por Hora"
        verbose_name_plural = "Pronósticos por Hora"
        unique_together = ('daily_forecast', 'time')

# ==============================================================================
# 4. Modelo WeatherAlert (Alertas/Cuidado)
# ==============================================================================

class WeatherAlert(models.Model):
    """Almacena alertas específicas de clima como 'Sandstorm' o 'Extreme Heat'."""
    
    daily_forecast = models.ForeignKey(DailyForecast, on_delete=models.CASCADE, related_name='alerts')
    type = models.CharField(max_length=100, help_text="Ej: Sandstorm, Extreme Heat")
    start_time = models.TimeField(help_text="Hora de inicio de la alerta (Ej: 21:00, 19:00)")
    date = models.DateField(help_text="Fecha de la alerta (Ej: Sep 12)")
    details = models.CharField(max_length=100, help_text="Ej: ssw 11 km/h")
    probability = models.IntegerField(help_text="Probabilidad de ocurrencia en % (Ej: 30%, 80%)")

    def __str__(self):
        return f"Alerta {self.type} - {self.daily_forecast.location.city}"

    class Meta:
        verbose_name = "Alerta Climática"
        verbose_name_plural = "Alertas Climáticas"


# ==============================================================================
# 5. Modelo FavoriteLocation (Ubicaciones Favoritas)
# ==============================================================================

class FavoriteLocation(models.Model):
    """Asocia una Location con un User para la pantalla de Favoritos."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    def __str__(self):
        return f"Favorito de {self.user.username}: {self.location.city}"

    class Meta:
        verbose_name = "Ubicación Favorita"
        verbose_name_plural = "Ubicaciones Favoritas"
        unique_together = ('user', 'location')