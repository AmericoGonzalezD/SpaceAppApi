import joblib
import pandas as pd
import numpy as np
import os

def predecir_condicion(lat, lon, dia):
    sin_day = np.sin(2 * np.pi * dia / 365)
    cos_day = np.cos(2 * np.pi * dia / 365)
    X_pred = pd.DataFrame([{"lat": lat, "lon": lon, "sin_day": sin_day, "cos_day": cos_day}])

    variables_fisicas = [
        "CO_surface_conc", "precipitation", "total_precip_rate",
        "specific_humidity", "temperature_surface", "skin_temperature",
        "wind_speed_10m", "avg_wind_speed_10m", "surface_pressure",
        "cloud_area", "frozen_precip", "snowfall", "uv_index",
        "dust_concentration", "SO2_concentration", "NO2_concentration",
        "O3_concentration", "potential_vorticity"
    ]
    
    preds = {}
    for var in variables_fisicas:
        modelo_path = f"app\\{var}_regressor.pkl"
        if os.path.exists(modelo_path):
            modelo = joblib.load(modelo_path)
            preds[var] = modelo.predict(X_pred)[0]
        else:
            preds[var] = None

    clf = joblib.load("app\\condition_classifier.pkl")
    df_pred = pd.DataFrame([{**preds, "lat": lat, "lon": lon, "sin_day": sin_day, "cos_day": cos_day}])
    df_pred = df_pred[clf.get_booster().feature_names]

    pred = clf.predict(df_pred)[0]
    classes = clf.classes_

    return {"lat": lat, "lon": lon, "day": dia, "condition": classes[pred], **preds}

if __name__ == "__main__":
    resultado = predecir_condicion(lat=100, lon=-20, dia=2)
    respuesta = np.array(list(resultado.values()), dtype=float)
    np.set_printoptions(suppress=True)

#   ['lat', 'lon', 'day', 'condition', 'CO_surface_conc', 'precipitation',
#  'total_precip_rate', 'specific_humidity', 'temperature_surface',
#  'skin_temperature', 'wind_speed_10m', 'avg_wind_speed_10m',
#  'surface_pressure', 'cloud_area', 'frozen_precip', 'snowfall',
#  'uv_index', 'dust_concentration', 'SO2_concentration',
#  'NO2_concentration', 'O3_concentration', 'potential_vorticity']
