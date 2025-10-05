# app/admin.py

from django.contrib import admin
# Importa todos tus modelos desde el archivo models.py de tu aplicación
from .models import Location, DailyForecast, HourlyForecast, WeatherAlert, FavoriteLocation


# Registra cada modelo en el sitio de administración
admin.site.register(Location)
admin.site.register(DailyForecast)
admin.site.register(HourlyForecast)
admin.site.register(WeatherAlert)
admin.site.register(FavoriteLocation)