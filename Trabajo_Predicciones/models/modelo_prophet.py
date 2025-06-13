import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
# 1. Cargar datos
df = pd.read_csv("C:\\Users\\pc\\Downloads\\datos_filtrados_2020_2023.csv")

# 2. Filtrar solo dengue SIN signos de alarma (opcional)
df = df[df['enfermedad'].str.contains('DENGUE', case=False)]

# 3. Crear columna fecha a partir de año y semana epidemiológica
# Para obtener el lunes de la semana epidemiológica
df['fecha'] = pd.to_datetime(df['ano'].astype(str) + '-W' + df['semana'].astype(str) + '-1', format='%Y-W%W-%w')

# 4. Agrupar casos por fecha (sumamos diagnostic si es numérico, si no contamos filas)
casos_semanales = df.groupby('fecha').size().reset_index(name='casos')

# 5. Preparar dataframe para Prophet
casos_semanales = casos_semanales.rename(columns={'fecha': 'ds', 'casos': 'y'})

# 6. Crear y entrenar modelo
model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
model.fit(casos_semanales)

# 7. Crear dataframe para predicciones futuras (12 semanas)
future = model.make_future_dataframe(periods=12, freq='W')

# 8. Predecir
forecast = model.predict(future)

# 9. Visualizar
model.plot(forecast)
plt.title('Predicción semanal de brotes de Dengue en Perú')
plt.show()

model.plot_components(forecast)
plt.show()

# 10. Mostrar las últimas predicciones (futuro)
print("\n🔹 Predicciones para las próximas 12 semanas:")
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(12))

# 11. Mostrar semanas con mayor predicción de casos
print("\n🔹 Semanas con mayor predicción de brotes:")
top_predicciones = forecast[['ds', 'yhat']].sort_values(by='yhat', ascending=False).head(5)
print(top_predicciones)

# 12. Mostrar tendencia general (última semana del modelo vs primera)
inicio = forecast['yhat'].iloc[0]
fin = forecast['yhat'].iloc[-1]
print(f"\n🔹 Tendencia general: de {inicio:.2f} casos estimados (inicio) a {fin:.2f} (fin)")

# 13. Comparar valor real vs predicho en la última semana con datos reales
print("\n🔹 Última semana real vs predicción:")
ultima_real = casos_semanales.tail(1)
prediccion_correspondiente = forecast[forecast['ds'] == ultima_real['ds'].values[0]]
print(f"Real: {ultima_real['y'].values[0]} casos")
print(f"Predicción: {prediccion_correspondiente['yhat'].values[0]:.2f} casos")


# Guardar las predicciones para las próximas 12 semanas
predicciones_futuras = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(12)
predicciones_futuras.to_csv("Trabajo_Predicciones/models/predicciones_futuras.csv", index=False)

# Guardar las semanas con mayor predicción de brotes
top_predicciones.to_csv("Trabajo_Predicciones/models/top_predicciones.csv", index=False)

# Guardar comparación última semana real vs predicción en un DataFrame y luego a CSV
comparacion_ultima_semana = pd.DataFrame({
    'ds': [ultima_real['ds'].values[0]],
    'casos_reales': [ultima_real['y'].values[0]],
    'casos_predichos': [prediccion_correspondiente['yhat'].values[0]]
})
comparacion_ultima_semana.to_csv("Trabajo_Predicciones/models/comparacion_ultima_semana.csv", index=False)

# 14. Comparar valores reales vs predichos en el periodo histórico
df_eval = pd.merge(casos_semanales, forecast[['ds', 'yhat']], on='ds', how='inner')

# Calcular métricas
rmse = np.sqrt(mean_squared_error(df_eval['y'], df_eval['yhat']))
mae = mean_absolute_error(df_eval['y'], df_eval['yhat'])
mape = np.mean(np.abs((df_eval['y'] - df_eval['yhat']) / df_eval['y'])) * 100
r2 = r2_score(df_eval['y'], df_eval['yhat'])

# Mostrar métricas
print("\n🔹 Métricas de evaluación del modelo:")
print(f"RMSE: {rmse:.2f}")
print(f"MAE: {mae:.2f}")
print(f"MAPE: {mape:.2f}%")
print(f"R²: {r2:.4f}")

# Guardar métricas en CSV
metricas_df = pd.DataFrame({
    'RMSE': [rmse],
    'MAE': [mae],
    'MAPE (%)': [mape],
    'R2': [r2]
})
metricas_df.to_csv("Trabajo_Predicciones/models/metricas_prophet.csv", index=False)

