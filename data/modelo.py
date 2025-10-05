import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBClassifier, XGBRegressor
import joblib

def modelo_regresor(df, variable_obj):
    predictores = ["lat", "lon", "sin_day", "cos_day"]

    tscv = TimeSeriesSplit(n_splits=5)
    parametros = {
        "n_estimators": [300, 500],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.01, 0.05],
        "subsample": [0.8],
        "colsample_bytree": [0.8]
    }

    resultados = {}
    for i in variable_obj:
        X, y = df[predictores], df[i]
        modelo = XGBRegressor(objective='reg:squarederror')
        grid = GridSearchCV(
        estimator=modelo,
        param_grid=parametros,
        cv=tscv,
        scoring="r2",
        verbose=1,
        n_jobs=-1
    )
        
        grid.fit(X, y)
        mejor_modelo = grid.best_estimator_
        joblib.dump(mejor_modelo, f"app\\{i}_regressor.pkl")

        y_pred = mejor_modelo.predict(X)
        resultados[i] = {
            "R2": r2_score(y, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y, y_pred))
        }

        print(f"{i}: R2 = {resultados[i]['R2']} | RMSE = {resultados[i]['RMSE']}")
    return resultados

def entrenar_modelo(df):
    
    entradas = ["lat", "lon", "sin_day", "cos_day",
        "CO_surface_conc", "precipitation", "total_precip_rate",
        "specific_humidity", "temperature_surface", "skin_temperature",
        "wind_speed_10m", "avg_wind_speed_10m", "surface_pressure",
        "cloud_area", "frozen_precip", "snowfall", "uv_index",
        "dust_concentration", "SO2_concentration", "NO2_concentration",
        "O3_concentration", "potential_vorticity"]
    
    entradas = [f for f in entradas if f in df.columns]

    X = df[entradas]
    y = LabelEncoder().fit_transform(df["condicion"])

    tscv = TimeSeriesSplit(n_splits=5)
    parametros = {
        "n_estimators": [300, 500],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.01, 0.05],
        "subsample": [0.8],
        "colsample_bytree": [0.8]
    }

    modelo = XGBClassifier(
        objective="multi:softprob",
        eval_metric="mlogloss",
        use_label_encoder=False
    )

    grid = GridSearchCV(
        estimator=modelo,
        param_grid=parametros,
        cv=tscv,
        scoring="f1_macro",
        verbose=1,
        n_jobs=-1
    )

    grid.fit(X, y)
    mejor_mdelo = grid.best_estimator_
    print("Mejores parametros: ", grid.best_params_)
    joblib.dump(mejor_mdelo, "app\condition_classifier.pkl")
    return mejor_mdelo

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
        try:
            modelo = joblib.load(f"app\\{var}_regressor.pkl")
            preds[var] = modelo.predict(X_pred)[0]
        except FileNotFoundError:
            preds[var] = None
    
    clf = joblib.load("app\\condition_classifier.pkl")
    df_pred = pd.DataFrame([{**preds, "lat": lat, "lon": lon, "sin_day": sin_day, "cos_day": cos_day}])
    df_pred = df_pred[clf.get_booster().feature_names]
    pred = clf.predict(df_pred)[0]
    classes = clf.classes_

    return {"lat": lat, "lon": lon, "day": dia, "condition": classes[pred], **preds}

if __name__ == "__main__":
    np.random.seed(125)
    n = 10_000

    days = np.random.randint(1, 366, n)
    sin_day = np.sin(2 * np.pi * days / 365)
    cos_day = np.cos(2 * np.pi * days / 365)

    lat = np.random.uniform(-90, 90, n)
    lon = np.random.uniform(-180, 180, n)

    # -----------------------------
    # Variables físicas coherentes
    # -----------------------------

    # Temperatura superficial (°C)
    temperature_surface = (
        25 + 10 * sin_day + np.random.normal(0, 3, n)
    )

    # Temperatura de la piel (°C)
    skin_temperature = temperature_surface + np.random.normal(0, 1, n)

    # Humedad específica (kg/kg)
    specific_humidity = (
        0.020 - 0.0004 * temperature_surface + np.random.normal(0, 0.001, n)
    )
    specific_humidity = np.clip(specific_humidity, 0.001, 0.03)

    # Nubosidad (0-1)
    cloud_area = (
        0.5 + 0.3 * np.cos(2 * np.pi * days / 365) + np.random.normal(0, 0.1, n)
    )
    cloud_area = np.clip(cloud_area, 0, 1)

    # Precipitación (mm/día)
    precipitation = (
        50 * np.maximum(0, cloud_area - 0.4) +
        np.random.exponential(scale=10, size=n)
    )

    # Tasa de precipitación (mm/h)
    total_precip_rate = precipitation / 24 + np.random.normal(0, 0.2, n)

    # Presión superficial (hPa)
    surface_pressure = 1013 - 5 * sin_day + np.random.normal(0, 3, n)

    # Velocidades del viento (m/s)
    wind_speed_10m = np.random.normal(5 + 3 * np.abs(sin_day), 2, n)
    avg_wind_speed_10m = wind_speed_10m - np.random.normal(0, 0.5, n)

    # Radiación UV (0-12)
    uv_index = (
        8 * np.maximum(0, sin_day) + np.random.normal(0, 1, n)
    )
    uv_index = np.clip(uv_index, 0, 12)

    # Nieve (mm)
    snowfall = np.where(temperature_surface < 0,
                        np.abs(np.random.normal(5, 3, n)),
                        0)

    # Precipitación congelada (mm)
    frozen_precip = snowfall * np.random.uniform(0.8, 1.2, n)

    # Concentración de CO (mg/m³)
    CO_surface_conc = (
        1.5 + 0.02 * precipitation - 0.03 * uv_index +
        np.random.normal(0, 0.3, n)
    )

    # Polvo (mg/m³)
    dust_concentration = np.clip(
        0.3 * np.maximum(0, 1 - cloud_area) + np.random.normal(0, 0.05, n),
        0, 0.5
    )

    # SO2 y NO2 (ppm)
    SO2_concentration = np.clip(
        0.05 + 0.02 * cloud_area + np.random.normal(0, 0.01, n),
        0, 0.2
    )
    NO2_concentration = np.clip(
        0.06 + 0.03 * np.maximum(0, 1 - uv_index/12) + np.random.normal(0, 0.01, n),
        0, 0.2
    )

    O3_concentration = np.clip(
        0.03 + 0.04 * uv_index/12 + np.random.normal(0, 0.01, n),
        0, 0.2
    )

    potential_vorticity = np.random.normal(0, 0.5, n)

    conditions = []
    for t, p, h, c in zip(temperature_surface, precipitation, specific_humidity, cloud_area):
        if t < 0:
            conditions.append("Nieve")
        elif p > 80:
            conditions.append("Lluvia")
        elif t > 32 and h < 0.015:
            conditions.append("Calor")
        elif c > 0.8:
            conditions.append("Nublado")
        else:
            conditions.append("Despejado")

    df = pd.DataFrame({
        "lat": lat, "lon": lon,
        "sin_day": sin_day, "cos_day": cos_day,
        "CO_surface_conc": CO_surface_conc,
        "precipitation": precipitation,
        "total_precip_rate": total_precip_rate,
        "specific_humidity": specific_humidity,
        "temperature_surface": temperature_surface,
        "skin_temperature": skin_temperature,
        "wind_speed_10m": wind_speed_10m,
        "avg_wind_speed_10m": avg_wind_speed_10m,
        "surface_pressure": surface_pressure,
        "cloud_area": cloud_area,
        "frozen_precip": frozen_precip,
        "snowfall": snowfall,
        "uv_index": uv_index,
        "dust_concentration": dust_concentration,
        "SO2_concentration": SO2_concentration,
        "NO2_concentration": NO2_concentration,
        "O3_concentration": O3_concentration,
        "potential_vorticity": potential_vorticity,
        "condicion": conditions
    })
    variables_objetivo = [
        "CO_surface_conc", "precipitation", "total_precip_rate",
        "specific_humidity", "temperature_surface", "skin_temperature",
        "wind_speed_10m", "avg_wind_speed_10m", "surface_pressure",
        "cloud_area", "frozen_precip", "snowfall", "uv_index",
        "dust_concentration", "SO2_concentration", "NO2_concentration",
        "O3_concentration", "potential_vorticity"
    ]

    # ======================================================
    # 3️⃣ Entrenar los modelos regresores
    # ======================================================
    print("\nEntrenando modelos regresores...")
    resultados = modelo_regresor(df, variables_objetivo)

    # ======================================================
    # 4️⃣ Entrenar el clasificador de condición
    # ======================================================
    print("\nEntrenando modelo clasificador de condición...")
    modelo_clasificador = entrenar_modelo(df)

    # ======================================================
    # 5️⃣ Realizar predicción final
    # ======================================================
    print("\nGenerando predicción...")
    prediccion = predecir_condicion(lat=25.6844, lon=-100.3181, dia=120)

    print("\nPredicción completa:")
    for k, v in prediccion.items():
        print(f"{k}: {v}")
