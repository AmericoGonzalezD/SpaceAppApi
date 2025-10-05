# app/seed.py

from app.models import (
    Location, 
    DailyForecast, 
    HourlyForecast, 
    WeatherAlert, 
    FavoriteLocation
)
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time
import random

def create_test_data():
    print("\n--- INICIANDO GENERACIÓN DE DATOS DE PRUEBA ---")

    # --- 1. Crear Ubicaciones Base (Locations) ---
    print("1. Creando ubicaciones...")
    locations_data = [
        ("Monterrey", "N.L.", "Mexico", 25.686614, -100.316113),
        ("Madrid", "Esp", "España", 40.416775, -3.703790),
        ("Nueva York", "NY", "USA", 40.712776, -74.005974),
        ("Tokio", "Tōkyō", "Japón", 35.689487, 139.691711),
    ]

    locations = []
    for city, state, country, lat, lon in locations_data:
        loc, created = Location.objects.get_or_create(
            city=city, 
            state_province=state, 
            country=country,
            latitude=lat,
            longitude=lon
        )
        locations.append(loc)
        if created:
            print(f"   -> Creada: {city}")

    # --- 2. Crear Pronósticos Diarios para cada Ubicación (20 Registros DailyForecast) ---
    print("\n2. Creando 20 pronósticos diarios...")
    daily_forecasts = []
    today = timezone.now().date()

    for loc in locations:
        for i in range(5):
            forecast_date = today + timedelta(days=i)
            
            temp = random.uniform(15.0, 35.0)
            max_t = temp + random.uniform(3.0, 5.0)
            min_t = temp - random.uniform(5.0, 7.0)
            feels = temp + 2.0
            
            conditions = random.choice(["Partly cloudy", "Sunny", "Rainy", "Heavy Clouds"])
            summary_text = f"Vientos de SW a SSW a {random.randint(10, 20)} km/h. La mínima nocturna será de {min_t:.1f}°C."

            df = DailyForecast.objects.create(
                location=loc,
                date=forecast_date,
                current_temp=temp,
                condition_summary=conditions,
                max_temp=max_t,
                min_temp=min_t,
                feels_like_temp=feels,
                humidity=random.randint(50, 90),
                precipitation_prob=random.randint(0, 80),
                wind_speed=random.uniform(5.0, 15.0),
                wind_direction=random.choice(["W", "NW", "SSW", "E"]),
                visibility=random.uniform(5.0, 15.0),
                pressure=random.uniform(1000.0, 1020.0),
                uv_index=random.choice(["Low 0", "Moderate 4", "High 8"]),
                air_quality=random.choice(["Low 0", "Moderate 3", "Bad 7"]),
                dew_point=random.uniform(10.0, 20.0),
                clouds=random.randint(30, 90),
                sunrise=time(5, 50, random.randint(0, 59)),
                sunset=time(18, 10, random.randint(0, 59)),
                summary=summary_text
            )
            daily_forecasts.append(df)
            # print(f"   -> Creado pronóstico para {loc.city} el {forecast_date}")


    # --- 3. Crear Datos por Hora y Alertas para los Primeros 2 Pronósticos ---
    print("\n3. Creando datos por hora y alertas...")
    for df in daily_forecasts[:2]: 
        for hour_offset in [8, 14, 20]:
            HourlyForecast.objects.create(
                daily_forecast=df,
                time=time(hour_offset, 0, 0),
                temperature=df.current_temp + random.uniform(-5.0, 5.0),
                condition=random.choice(["Clear", "Light Rain", "Windy"]),
                precipitation_perc=random.randint(0, 50)
            )
        
        if df.location.city == "Monterrey":
            WeatherAlert.objects.create(
                daily_forecast=df,
                type="Extreme Heat",
                start_time=time(15, 0),
                date=df.date,
                details="ssw 15 km/h",
                probability=80
            )
    print("   -> Generación de detalles de prueba completada.")

    # --- 4. Crear 2 Registros de Favoritos (Requiere un Usuario) ---
    print("\n4. Creando favoritos...")
    if User.objects.exists():
        user = User.objects.first()
        FavoriteLocation.objects.get_or_create(user=user, location=locations[0])
        FavoriteLocation.objects.get_or_create(user=user, location=locations[1])
        print(f"   -> Creados 2 favoritos para el usuario: {user.username}")
    else:
        print("   -> AVISO: No se crearon Favoritos. ¡Crea un superusuario primero!")

    print("\n--- GENERACIÓN DE DATOS DE PRUEBA FINALIZADA CON ÉXITO ---")


if __name__ == '__main__':
    create_test_data()