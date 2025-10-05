# app/utils.py

import joblib
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import date, time
from decimal import Decimal, InvalidOperation # Importado para el FIX de DecimalField
from django.utils import timezone

# Asegúrate de que tu modelo tenga la aplicación correcta
from app.models import Location, DailyForecast 


# Define la ruta base del proyecto (un nivel más arriba de la carpeta 'app')
BASE_DIR = Path(__file__).resolve().parent.parent

# Mapeo de variables: script_key (salida del modelo) -> model_key (campo de Django)
VARIABLE_MAP = {
    "CO_surface_conc": "CO_surface_conc", 
    "precipitation": "precipitation_prob",
    "total_precip_rate": "total_precip_rate",
    "specific_humidity": "specific_humidity_pred",
    "temperature_surface": "current_temp", # Mapeado como temperatura base
    "skin_temperature": "skin_temperature",
    "wind_speed_10m": "wind_speed", # Mapeado a wind_speed
    "avg_wind_speed_10m": "avg_wind_speed_10m",
    "surface_pressure": "surface_pressure_pred",
    "cloud_area": "cloud_area_pred",
    "frozen_precip": "frozen_precip",
    "snowfall": "snowfall_pred",
    "uv_index": "uv_index", 
    "dust_concentration": "dust_concentration",
    "SO2_concentration": "SO2_concentration",
    "NO2_concentration": "NO2_concentration",
    "O3_concentration": "O3_concentration",
    "potential_vorticity": "potential_vorticity",
}


def predecir_condicion(lat, lon, dia):
    """
    Ejecuta el modelo de predicción de Python usando archivos PKL.
    """
    sin_day = np.sin(2 * np.pi * dia / 365)
    cos_day = np.cos(2 * np.pi * dia / 365)
    X_pred = pd.DataFrame([{"lat": lat, "lon": lon, "sin_day": sin_day, "cos_day": cos_day}])

    variables_fisicas = list(VARIABLE_MAP.keys())
    preds = {}
    
    # 1. Predecir variables físicas usando modelos regresores
    for var in variables_fisicas:
        # RUTA CORREGIDA: Busca en 'data/app'
        modelo_path = BASE_DIR / "data" / "app" / f"{var}_regressor.pkl" 
        
        if modelo_path.exists():
            modelo = joblib.load(modelo_path)
            # Asegura que las features del input coincidan con las que espera el modelo
            X_model_features = X_pred[[col for col in X_pred.columns if col in modelo.feature_names_in_]]
            preds[var] = modelo.predict(X_model_features)[0]
        else:
            print(f"ERROR: Archivo regresor no encontrado para {var} en: {modelo_path}")
            preds[var] = 0.0 

    # 2. Clasificar la condición principal
    # RUTA CORREGIDA: Busca en 'data/app'
    clf_path = BASE_DIR / "data" / "app" / "condition_classifier.pkl"
    
    condition = "Not Classified"
    if clf_path.exists():
        clf = joblib.load(clf_path)
        
        # Preparar DataFrame para el clasificador
        df_pred = pd.DataFrame([{**preds, "lat": lat, "lon": lon, "sin_day": sin_day, "cos_day": cos_day}])
        feature_names = list(clf.get_booster().feature_names)
        df_pred = df_pred[[col for col in feature_names if col in df_pred.columns]]
        
        pred = clf.predict(df_pred)[0]
        classes = clf.classes_
        condition = classes[int(pred)] 
    else:
        print(f"ERROR: Archivo clasificador no encontrado en: {clf_path}")

    return {"lat": lat, "lon": lon, "day": dia, "condition": condition, **preds}


def predecir_y_guardar_pronostico(lat, lon, forecast_date):
    """
    Ejecuta el modelo de predicción, mapea los resultados y guarda/actualiza
    el registro DailyForecast en la base de datos.
    """
    dia_del_año = forecast_date.timetuple().tm_yday
    
    # 1. Ejecutar la predicción
    pred_data = predecir_condicion(lat, lon, dia_del_año)
    
    # 2. Buscar/Crear la Ubicación (Para asegurar el ForeignKey)
    tolerance = 0.01
    try:
        # Buscamos la Location con una pequeña tolerancia
        location = Location.objects.get(
            latitude__gte=lat - tolerance, latitude__lte=lat + tolerance,
            longitude__gte=lon - tolerance, longitude__lte=lon + tolerance
        )
    except Location.DoesNotExist:
        # Si la ubicación no existe, la creamos
        location = Location.objects.create(
            city=f"Predicción @ Lat {lat:.4f}",
            latitude=lat,
            longitude=lon
        )
    except Location.MultipleObjectsReturned:
        # Si hay duplicados (como sucedió en la prueba anterior), tomamos el primero
        location = Location.objects.filter(
            latitude__gte=lat - tolerance, latitude__lte=lat + tolerance,
            longitude__gte=lon - tolerance, longitude__lte=lon + tolerance
        ).first()


    # 3. Mapear y Limpiar Datos para Django
    data_to_save = {
        'location': location,
        'date': forecast_date,
        'condition_summary': pred_data['condition'],
    }
    
    # Obtener el valor de temperatura superficial (base para max/min)
    base_temp_val = pred_data.get('temperature_surface')

    # 🚨 FIX: Asignar valores derivados obligatorios para evitar 'cannot be null' 🚨
    if base_temp_val is not None:
        try:
            temp = Decimal(str(base_temp_val))
            # Asignaciones básicas y derivadas (para rellenar los campos obligatorios)
            data_to_save['current_temp'] = temp
            data_to_save['max_temp'] = temp + Decimal('5.0')
            data_to_save['min_temp'] = temp - Decimal('5.0')
            data_to_save['feels_like_temp'] = temp + Decimal('2.0')
            data_to_save['humidity'] = 70 # Default para el campo IntegerField
            data_to_save['precipitation_prob'] = 20 # Default para el campo IntegerField
            data_to_save['wind_speed'] = Decimal('10.0') # Default
            data_to_save['wind_direction'] = "SW" # Default
            data_to_save['visibility'] = Decimal('10.0') # Default
            data_to_save['pressure'] = Decimal('1010.00') # Default (Corregido a 7 digitos en models.py)
            data_to_save['dew_point'] = temp - Decimal('5.0') # Default
            data_to_save['clouds'] = Decimal('50.0') # Default
            
        except InvalidOperation:
            # Si el valor base no es numérico, saltamos esta asignación (debería ser corregido en el modelo ML)
            print(f"Advertencia: Temperatura base inválida: {base_temp_val}")
            
    # Mapeo de Variables Físicas Científicas
    for script_key, model_key in VARIABLE_MAP.items():
        value = pred_data.get(script_key)
        
        # Saltamos si el valor ya fue mapeado en el bloque de FIX (ej: current_temp, wind_speed)
        if model_key in data_to_save.keys() and model_key != script_key:
            continue
            
        if value is None:
            continue
            
        try:
            if model_key == 'precipitation_prob':
                data_to_save[model_key] = int(np.clip(value, 0, 100))
            elif model_key == 'uv_index':
                data_to_save[model_key] = f"Index {int(np.clip(value, 0, 15))}"
            else:
                # FIX: Convierte a string antes de crear Decimal
                data_to_save[model_key] = Decimal(str(value))
        except (ValueError, InvalidOperation, TypeError):
             print(f"Advertencia: Error de conversión para {model_key} con valor {value}. Se omite.")

    # 4. Guardar/Actualizar en la Base de Datos
    forecast, created = DailyForecast.objects.update_or_create(
        location=location,
        date=forecast_date,
        defaults=data_to_save
    )

    return forecast, created