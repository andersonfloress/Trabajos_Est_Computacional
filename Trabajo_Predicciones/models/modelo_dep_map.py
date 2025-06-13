import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from statsmodels.tsa.arima.model import ARIMA
import warnings

# 1. Cargar datos
df = pd.read_csv("C:\\Users\\pc\\Downloads\\casos_por_departamento_ano_2020_2023.csv")
geo_path = "Trabajo_Predicciones\\Visualizaciones\\pe.json"
peru_map = gpd.read_file(geo_path)

# 2. Normalizar nombres
df['departamento'] = df['departamento'].str.strip().str.lower()
peru_map['name'] = peru_map['name'].str.strip().str.lower()

# 3. Calcular predicciones y totales históricos
departamentos = df['departamento'].unique()
predicciones = []
totales_hist = []

warnings.filterwarnings("ignore")  # Ignorar warnings de ARIMA

for depto in departamentos:
    df_depto = df[df['departamento'] == depto].sort_values(by='ano')
    
    if df_depto.shape[0] < 3:
        continue  # No hay suficiente data

    y = df_depto['total_casos'].values

    try:
        # ARIMA(1,1,1) es un modelo común; puedes ajustar p,d,q según sea necesario
        model = ARIMA(y, order=(1, 1, 1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=1)  # Predecir solo 2024
        pred_2024 = forecast[0]
    except:
        pred_2024 = 0  # Si hay error, poner 0 como fallback

    total_hist = y.sum()
    totales_hist.append({'departamento': depto, 'total_hist': total_hist})
    predicciones.append({
        'departamento': depto,
        'prediccion_2024': max(0, int(round(pred_2024)))
    })

# 4. Unir en DataFrame
df_tot = pd.DataFrame(totales_hist).set_index('departamento')
df_pred = pd.DataFrame(predicciones).set_index('departamento')
df_comb = pd.concat([df_tot, df_pred], axis=1).sort_values('total_hist')

# 5. Gráfico de barras horizontales
plt.figure(figsize=(10, 10))
y_pos = np.arange(len(df_comb))
bar_width = 0.4

plt.barh(y_pos - bar_width/2, df_comb['total_hist'], height=bar_width, label='Total 2020-2023', color='skyblue')
plt.barh(y_pos + bar_width/2, df_comb['prediccion_2024'], height=bar_width, label='Predicción 2024', color='salmon')

plt.yticks(y_pos, df_comb.index.str.upper())
plt.xlabel('Casos de dengue')
plt.title('Total de casos históricos y predicción 2024 por departamento (ARIMA)')
plt.legend()
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# 6. Guardar CSV
df_csv = df_comb.reset_index()
df_csv['departamento'] = df_csv['departamento'].str.upper()
df_csv.to_csv("Trabajo_Predicciones\\models\\casosTotales_predicciones_2024.csv", index=False)
print("CSV guardado con totales y predicciones (ARIMA).")

# 7. Mapa de calor
peru_map = peru_map.rename(columns={"name": "departamento"})
gdf_merged = peru_map.merge(df_comb.reset_index(), on="departamento", how='left')
gdf_merged['prediccion_2024'] = gdf_merged['prediccion_2024'].fillna(0).astype(int)

fig, ax = plt.subplots(1, 1, figsize=(12, 10))
gdf_merged.plot(column='prediccion_2024',
                cmap='OrRd',
                linewidth=0.8,
                edgecolor='0.8',
                legend=True,
                legend_kwds={'label': "Casos predichos 2024 (ARIMA)"},
                ax=ax)

for idx, row in gdf_merged.iterrows():
    centroid = row['geometry'].centroid
    valor = int(row['prediccion_2024'])
    ax.plot(centroid.x, centroid.y, 'ko', markersize=3)
    ax.text(centroid.x, centroid.y, str(valor), fontsize=9, ha='center', va='bottom', color='black', fontweight='bold')

ax.set_title('Predicción de casos de dengue 2024 por departamento - Perú (ARIMA)', fontsize=14)
ax.axis('off')
plt.tight_layout()
plt.savefig("Trabajo_Predicciones\\models\\mapa_prediccion_dengue.png", dpi=300)
plt.show()

print("Mapa de predicción guardado correctamente (ARIMA).")

