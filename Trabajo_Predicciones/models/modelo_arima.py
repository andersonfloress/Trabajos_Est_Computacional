import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from pandas.plotting import register_matplotlib_converters
import warnings
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

warnings.filterwarnings("ignore")
register_matplotlib_converters()

# 1. Cargar datos
df = pd.read_csv("C:\\Users\\pc\\Downloads\\datos_filtrados_2020_2023.csv")

# 2. Filtrar solo dengue (puedes ajustar a lo que quieras)
df = df[df['enfermedad'].str.contains('DENGUE', case=False)]

# 3. Crear columna de fecha desde año y semana
df['fecha'] = pd.to_datetime(df['ano'].astype(str) + '-W' + df['semana'].astype(str) + '-1', format='%Y-W%W-%w')

# 4. Agrupar por semana (contar casos)
casos_semanales = df.groupby('fecha').size().reset_index(name='casos')
casos_semanales.set_index('fecha', inplace=True)

# 5. Ajustar modelo ARIMA (p, d, q) → puedes experimentar con (1,1,1), (2,1,2), etc.
modelo_arima = ARIMA(casos_semanales['casos'], order=(1, 1, 1))
modelo_entrenado = modelo_arima.fit()

# 6. Predicción para las próximas 12 semanas
n_semanas = 12
predicciones = modelo_entrenado.forecast(steps=n_semanas)

# 7. Crear índice de fechas futuras
ultima_fecha = casos_semanales.index[-1]
fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(weeks=1), periods=n_semanas, freq='W')

# 8. Visualizar resultados
plt.figure(figsize=(12, 6))
plt.plot(casos_semanales.index, casos_semanales['casos'], label='Casos reales')
plt.plot(fechas_futuras, predicciones, label='Predicción ARIMA', color='red')
plt.title('Predicción de casos semanales de dengue con ARIMA')
plt.xlabel('Fecha')
plt.ylabel('Casos')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 9. Mostrar datos en consola
print("\n🔹 Predicciones ARIMA para las próximas 12 semanas:")
for fecha, valor in zip(fechas_futuras, predicciones):
    print(f"{fecha.date()}: {round(valor)} casos estimados")

# Guardar predicciones en CSV
df_predicciones = pd.DataFrame({
    'fecha': fechas_futuras,
    'prediccion_casos': predicciones.round().astype(int)
})
df_predicciones.to_csv("Trabajo_Predicciones/models/predicciones_arima.csv", index=False)

# 10. Tendencia general
inicio = casos_semanales['casos'].iloc[0]
fin = predicciones.iloc[-1]
print(f"\n🔹 Tendencia general: de {inicio} casos (inicio histórico) a {round(fin)} casos (última predicción)")

# Guardar tendencia general en CSV
df_tendencia = pd.DataFrame({
    'descripcion': ['inicio_historico', 'ultima_prediccion'],
    'casos': [inicio, round(fin)]
})
df_tendencia.to_csv("Trabajo_Predicciones/models/tendencia_general_Arima.csv", index=False)

# 11. Última semana real
ultima_semana_real = casos_semanales.tail(1)
print("\n🔹 Última semana real:")
print(ultima_semana_real)

# Guardar última semana real en CSV
ultima_semana_real.to_csv("Trabajo_Predicciones/models/ultima_semana_real_Arima.csv", index=False)

# 12. Evaluar modelo ARIMA en datos históricos
predicciones_in_sample = modelo_entrenado.predict(start=0, end=len(casos_semanales)-1)

# Crear DataFrame para comparar
df_eval_arima = casos_semanales.copy()
df_eval_arima['prediccion'] = predicciones_in_sample

# Calcular métricas
rmse_arima = np.sqrt(mean_squared_error(df_eval_arima['casos'], df_eval_arima['prediccion']))
mae_arima = mean_absolute_error(df_eval_arima['casos'], df_eval_arima['prediccion'])
mape_arima = np.mean(np.abs((df_eval_arima['casos'] - df_eval_arima['prediccion']) / df_eval_arima['casos'])) * 100
r2_arima = r2_score(df_eval_arima['casos'], df_eval_arima['prediccion'])

# Mostrar métricas
print("\n🔹 Métricas de evaluación del modelo ARIMA:")
print(f"RMSE: {rmse_arima:.2f}")
print(f"MAE: {mae_arima:.2f}")
print(f"MAPE: {mape_arima:.2f}%")
print(f"R²: {r2_arima:.4f}")

# Guardar métricas en CSV
metricas_arima_df = pd.DataFrame({
    'RMSE': [rmse_arima],
    'MAE': [mae_arima],
    'MAPE (%)': [mape_arima],
    'R2': [r2_arima]
})
metricas_arima_df.to_csv("Trabajo_Predicciones/models/metricas_arima.csv", index=False)
